"use strict";

const assert = require("node:assert/strict");
const { test } = require("node:test");
const sharp = require("sharp");
const { decodePng, encodePng, getCapacity, SteganographyError } = require("../src/core");
const { app, createApp } = require("../src/server");

async function coverImage(width = 128, height = 128) {
  return sharp({
    create: {
      width,
      height,
      channels: 3,
      background: { r: 91, g: 137, b: 201 },
    },
  }).png().toBuffer();
}

async function withApiServer(handler, api = app) {
  const server = await new Promise((resolve) => {
    const listener = api.listen(0, "127.0.0.1", () => resolve(listener));
  });
  try {
    await handler(`http://127.0.0.1:${server.address().port}`);
  } finally {
    await new Promise((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
    });
  }
}

function corruptIdat(png) {
  const corrupted = Buffer.from(png);
  let offset = 8;
  while (offset + 12 <= corrupted.length) {
    const length = corrupted.readUInt32BE(offset);
    const type = corrupted.toString("ascii", offset + 4, offset + 8);
    if (type === "IDAT" && length > 0) {
      corrupted[offset + 8 + Math.floor(length / 2)] ^= 0xff;
      return corrupted;
    }
    offset += length + 12;
  }
  throw new Error("PNG did not contain an IDAT chunk.");
}

async function postDecode(baseUrl, image) {
  return fetch(`${baseUrl}/api/decode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: image.toString("base64"), password: "not relevant" }),
  });
}

test("encodes and decodes UTF-8 messages", async () => {
  const cover = await coverImage();
  const encoded = await encodePng(cover, "hello, こんにちは 🌍", "correct horse battery staple");

  assert.equal(await decodePng(encoded, "correct horse battery staple"), "hello, こんにちは 🌍");
});

test("rejects incorrect passwords and modified payloads", async () => {
  const cover = await coverImage();
  const encoded = await encodePng(cover, "secret", "password");

  await assert.rejects(
    decodePng(encoded, "wrong"),
    (error) => error instanceof SteganographyError && /Incorrect password/.test(error.message),
  );

  const { data, info } = await sharp(encoded).raw().toBuffer({ resolveWithObject: true });
  data[36 * 8] ^= 1;
  const modified = await sharp(data, {
    raw: { width: info.width, height: info.height, channels: info.channels },
  }).png().toBuffer();
  await assert.rejects(
    decodePng(modified, "password"),
    (error) => error instanceof SteganographyError && /Incorrect password/.test(error.message),
  );
});

test("reports capacity and rejects messages that do not fit", async () => {
  const cover = await coverImage(16, 16);
  const capacity = await getCapacity(cover);

  assert.equal(capacity.maxMessageBytes, Math.max(0, Math.floor((16 * 16 * 3) / 8) - 36 - 16));
  await assert.rejects(
    encodePng(cover, "x".repeat(1_000), "password"),
    (error) => error instanceof SteganographyError && /capacity/.test(error.message),
  );
});

test("API returns sanitized 400 errors for invalid PNG input", async () => {
  const validPng = await coverImage();
  const jpeg = await sharp(validPng).jpeg().toBuffer();
  const malformedImages = [
    Buffer.from("not an image"),
    corruptIdat(validPng),
    validPng.subarray(0, Math.floor(validPng.length / 2)),
    jpeg,
  ];

  await withApiServer(async (baseUrl) => {
    for (const image of malformedImages) {
      const response = await postDecode(baseUrl, image);
      const text = await response.text();
      assert.equal(response.status, 400, text);
      assert.doesNotMatch(text, /sharp|vips/i);
      assert.equal(typeof JSON.parse(text).error, "string");
    }
  });
});

test("API encodes and decodes without caching responses", async () => {
  const cover = await coverImage();
  await withApiServer(async (baseUrl) => {
    const encodedResponse = await fetch(`${baseUrl}/api/encode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: cover.toString("base64"),
        message: "API round trip",
        password: "password",
      }),
    });
    assert.equal(encodedResponse.status, 200);
    assert.match(encodedResponse.headers.get("content-type"), /image\/png/);
    assert.match(encodedResponse.headers.get("cache-control"), /no-store/);
    const encoded = Buffer.from(await encodedResponse.arrayBuffer());

    const decodedResponse = await fetch(`${baseUrl}/api/decode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: encoded.toString("base64"), password: "password" }),
    });
    assert.equal(decodedResponse.status, 200);
    assert.deepEqual(await decodedResponse.json(), { message: "API round trip" });
    assert.match(decodedResponse.headers.get("cache-control"), /no-store/);
  });
});

test("rate limits oversized JSON before parsing the request body", async () => {
  const api = createApp({ bodyLimit: "16b" });
  const oversizedBody = JSON.stringify({ data: "x".repeat(32) });

  await withApiServer(async (baseUrl) => {
    for (let requestNumber = 0; requestNumber < 20; requestNumber += 1) {
      const response = await fetch(`${baseUrl}/api/encode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: oversizedBody,
      });
      assert.equal(response.status, 413);
      await response.arrayBuffer();
    }

    const limitedResponse = await fetch(`${baseUrl}/api/encode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: oversizedBody,
    });
    assert.equal(limitedResponse.status, 429);
    assert.match((await limitedResponse.json()).error, /rate limit/i);
  }, api);
});

test("rejects jobs beyond the configured concurrency limit", async () => {
  let releaseSlowEncode;
  let markEncodeStarted;
  const slowEncode = new Promise((resolve) => {
    releaseSlowEncode = resolve;
  });
  const encodeStarted = new Promise((resolve) => {
    markEncodeStarted = resolve;
  });
  const api = createApp({
    maxConcurrentJobs: 1,
    encodePng: async () => {
      markEncodeStarted();
      await slowEncode;
      return Buffer.from("test image");
    },
  });
  const request = () => fetch(`${baseUrl}/api/encode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: "eA==", message: "test", password: "password" }),
  });

  let baseUrl;
  await withApiServer(async (serverUrl) => {
    baseUrl = serverUrl;
    try {
      const firstResponsePromise = request();
      await encodeStarted;
      const busyResponse = await request();
      assert.equal(busyResponse.status, 503);
      assert.equal(busyResponse.headers.get("retry-after"), "1");
      assert.match((await busyResponse.json()).error, /busy/i);

      releaseSlowEncode();
      assert.equal((await firstResponsePromise).status, 200);
    } finally {
      releaseSlowEncode();
    }
  }, api);
});
