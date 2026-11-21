"use strict";

const assert = require("node:assert/strict");
const { createCipheriv, pbkdf2Sync } = require("node:crypto");
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

async function encodeLegacyImage(imageBuffer, message, password) {
  const { data, info } = await sharp(imageBuffer)
    .toColourspace("srgb")
    .removeAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  const salt = Buffer.alloc(16, 1);
  const nonce = Buffer.alloc(12, 2);
  const plaintext = Buffer.from(message, "utf8");
  const header = Buffer.alloc(36);
  Buffer.from("STG2", "ascii").copy(header);
  salt.copy(header, 4);
  nonce.copy(header, 20);
  header.writeUInt32BE(plaintext.length + 16, 32);
  const key = pbkdf2Sync(password, salt, 600_000, 32, "sha256");
  const cipher = createCipheriv("aes-256-gcm", key, nonce);
  cipher.setAAD(header);
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final(), cipher.getAuthTag()]);
  const payload = Buffer.concat([header, ciphertext]);

  let bitIndex = 0;
  for (const byte of payload) {
    for (let shift = 7; shift >= 0; shift -= 1) {
      data[bitIndex] = (data[bitIndex] & 0xfe) | ((byte >> shift) & 1);
      bitIndex += 1;
    }
  }
  const encoded = await sharp(data, {
    raw: { width: info.width, height: info.height, channels: 3 },
  }).png().toBuffer();
  key.fill(0);
  plaintext.fill(0);
  data.fill(0);
  return encoded;
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

test("requires strong new passwords while decoding legacy short passwords", async () => {
  const cover = await coverImage();
  await assert.rejects(
    encodePng(cover, "new message", "x".repeat(11)),
    /at least 12 characters/,
  );
  const unicodePassword = "🌍".repeat(12);
  const unicodeEncoded = await encodePng(cover, "unicode password", unicodePassword);
  assert.equal(await decodePng(unicodeEncoded, unicodePassword), "unicode password");

  const legacy = await encodeLegacyImage(cover, "legacy message", "legacy");
  assert.equal(await decodePng(legacy, "legacy"), "legacy message");
});

test("rejects incorrect passwords and modified payloads", async () => {
  const cover = await coverImage();
  const encoded = await encodePng(cover, "secret", "correct horse battery staple");

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
    decodePng(modified, "correct horse battery staple"),
    (error) => error instanceof SteganographyError && /Incorrect password/.test(error.message),
  );
});

test("reports capacity and rejects messages that do not fit", async () => {
  const cover = await coverImage(16, 16);
  const capacity = await getCapacity(cover);

  assert.equal(capacity.maxMessageBytes, Math.max(0, Math.floor((16 * 16 * 3) / 8) - 36 - 16));
  await assert.rejects(
    encodePng(cover, "x".repeat(1_000), "correct horse battery staple"),
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
        password: "correct horse battery staple",
      }),
    });
    assert.equal(encodedResponse.status, 200);
    assert.match(encodedResponse.headers.get("content-type"), /image\/png/);
    assert.match(encodedResponse.headers.get("cache-control"), /no-store/);
    const encoded = Buffer.from(await encodedResponse.arrayBuffer());

    const decodedResponse = await fetch(`${baseUrl}/api/decode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: encoded.toString("base64"),
        password: "correct horse battery staple",
      }),
    });
    assert.equal(decodedResponse.status, 200);
    assert.deepEqual(await decodedResponse.json(), { message: "API round trip" });
    assert.match(decodedResponse.headers.get("cache-control"), /no-store/);
  });
});

test("API rejects short passwords for new encodings", async () => {
  const cover = await coverImage();

  await withApiServer(async (baseUrl) => {
    const response = await fetch(`${baseUrl}/api/encode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: cover.toString("base64"),
        message: "new message",
        password: "short",
      }),
    });
    assert.equal(response.status, 400);
    assert.match((await response.json()).error, /at least 12 characters/);
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
    body: JSON.stringify({
      image: "eA==",
      message: "test",
      password: "correct horse battery staple",
    }),
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
