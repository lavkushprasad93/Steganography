"use strict";

const cors = require("cors");
const express = require("express");
const { rateLimit } = require("express-rate-limit");
const helmet = require("helmet");
const {
  MAX_IMAGE_BYTES,
  MAX_MESSAGE_BYTES,
  MAX_PASSWORD_BYTES,
  SteganographyError,
  decodePng,
  encodePng,
  getCapacity,
} = require("./core");

const PORT = Number(process.env.PORT || 8000);

class RequestError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.status = status;
  }
}

function positiveIntegerFromEnv(name, defaultValue) {
  const raw = process.env[name];
  if (raw === undefined || raw.trim() === "") return defaultValue;
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < 1) {
    throw new Error(`${name} must be a positive integer.`);
  }
  return value;
}

function validateObject(body, requiredFields) {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new RequestError("Request body must be a JSON object.");
  }
  for (const field of requiredFields) {
    if (!(field in body)) {
      throw new RequestError(`Missing required field: ${field}.`);
    }
  }
}

function decodeImageField(value) {
  if (typeof value !== "string" || value.length === 0 || value.length % 4 !== 0) {
    throw new RequestError("Image must be base64-encoded PNG data.");
  }
  const maxEncodedLength = Math.ceil(MAX_IMAGE_BYTES / 3) * 4;
  if (value.length > maxEncodedLength || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
    throw new RequestError("Image must be valid base64 data under 5 MB.");
  }
  const image = Buffer.from(value, "base64");
  if (image.length === 0 || image.length > MAX_IMAGE_BYTES || image.toString("base64") !== value) {
    image.fill(0);
    throw new RequestError("Image must be valid base64 data under 5 MB.");
  }
  return image;
}

function validatePassword(password) {
  if (typeof password !== "string" || password.length === 0) {
    throw new RequestError("Password must not be empty.");
  }
  if (Buffer.byteLength(password, "utf8") > MAX_PASSWORD_BYTES) {
    throw new RequestError("Password must be 1024 bytes or fewer.");
  }
}

function createApp(options = {}) {
  const rateLimitPerMinute = options.rateLimitPerMinute
    ?? positiveIntegerFromEnv("RATE_LIMIT_PER_MINUTE", 20);
  const maxConcurrentJobs = options.maxConcurrentJobs
    ?? positiveIntegerFromEnv("MAX_CONCURRENT_JOBS", 2);
  const bodyLimit = options.bodyLimit || "8mb";
  const encodeImage = options.encodePng || encodePng;
  const decodeImage = options.decodePng || decodePng;
  const readCapacity = options.getCapacity || getCapacity;
  const allowedOrigins = new Set(
    (process.env.WEB_ORIGINS || "http://localhost:5173")
      .split(",")
      .map((origin) => origin.trim())
      .filter(Boolean),
  );
  const app = express();
  let activeJobs = 0;

  app.disable("x-powered-by");
  app.set("trust proxy", 1);
  app.use(helmet());
  app.use(cors({
    origin(origin, callback) {
      callback(null, !origin || allowedOrigins.has(origin));
    },
    methods: ["GET", "POST"],
    allowedHeaders: ["Content-Type"],
  }));
  app.use((request, response, next) => {
    response.setHeader("Cache-Control", "no-store, max-age=0");
    response.setHeader("Pragma", "no-cache");
    const releaseRequestBody = () => {
      request.body = undefined;
    };
    response.once("finish", releaseRequestBody);
    response.once("close", releaseRequestBody);
    next();
  });
  app.use("/api", rateLimit({
    windowMs: 60_000,
    limit: rateLimitPerMinute,
    standardHeaders: "draft-7",
    legacyHeaders: false,
    skip: (request) => request.path === "/health",
    handler: (_request, response) => {
      response.status(429).json({ error: "Rate limit exceeded. Try again later." });
    },
  }));
  app.use(express.json({ limit: bodyLimit, strict: true }));

  function withConcurrentJob(handler) {
    return async (request, response, next) => {
      if (activeJobs >= maxConcurrentJobs) {
        response.setHeader("Retry-After", "1");
        response.status(503).json({ error: "Server is busy. Try again shortly." });
        return;
      }
      activeJobs += 1;
      try {
        await handler(request, response, next);
      } catch (error) {
        next(error);
      } finally {
        activeJobs -= 1;
      }
    };
  }

  app.get("/api/health", (_request, response) => {
    response.json({ status: "ok" });
  });

  app.post("/api/capacity", withConcurrentJob(async (request, response, next) => {
    let image;
    try {
      validateObject(request.body, ["image"]);
      image = decodeImageField(request.body.image);
      response.json(await readCapacity(image));
    } catch (error) {
      next(error);
    } finally {
      if (image) image.fill(0);
    }
  }));

  app.post("/api/encode", withConcurrentJob(async (request, response, next) => {
    let image;
    let output;
    try {
      validateObject(request.body, ["image", "message", "password"]);
      if (typeof request.body.message !== "string" || request.body.message.length === 0) {
        throw new RequestError("Message must not be empty.");
      }
      if (Buffer.byteLength(request.body.message, "utf8") > MAX_MESSAGE_BYTES) {
        throw new RequestError("Message exceeds the 1 MB limit.", 413);
      }
      validatePassword(request.body.password);
      image = decodeImageField(request.body.image);
      output = await encodeImage(image, request.body.message, request.body.password);
      request.body = undefined;
      response.once("finish", () => output.fill(0));
      response.once("close", () => output.fill(0));
      response.type("png").attachment("stego-image.png").send(output);
    } catch (error) {
      next(error);
    } finally {
      if (image) image.fill(0);
    }
  }));

  app.post("/api/decode", withConcurrentJob(async (request, response, next) => {
    let image;
    try {
      validateObject(request.body, ["image", "password"]);
      validatePassword(request.body.password);
      image = decodeImageField(request.body.image);
      const message = await decodeImage(image, request.body.password);
      request.body = undefined;
      response.json({ message });
    } catch (error) {
      next(error);
    } finally {
      if (image) image.fill(0);
    }
  }));

  app.use((error, _request, response, _next) => {
    if (response.headersSent) return;
    if (error instanceof RequestError || error instanceof SteganographyError) {
      response.status(error.status || 400).json({ error: error.message });
      return;
    }
    if (error && error.type === "entity.too.large") {
      response.status(413).json({ error: "Request exceeds the configured JSON body limit." });
      return;
    }
    if (error && error.type === "entity.parse.failed") {
      response.status(400).json({ error: "Request body must be valid JSON." });
      return;
    }
    console.error("Unhandled API error:", error instanceof Error ? error.name : "UnknownError");
    response.status(500).json({ error: "Request could not be processed." });
  });

  return app;
}

const app = createApp();

if (require.main === module) {
  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Steganography API listening on port ${PORT}`);
  });
}

module.exports = { app, createApp };
