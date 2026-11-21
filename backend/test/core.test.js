"use strict";

const assert = require("node:assert/strict");
const { test } = require("node:test");
const sharp = require("sharp");
const { decodePng, encodePng, getCapacity, SteganographyError } = require("../src/core");
const { app } = require("../src/server");

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

test("API encodes and decodes without caching responses", async () => {
  const cover = await coverImage();
  const server = await new Promise((resolve) => {
    const listener = app.listen(0, "127.0.0.1", () => resolve(listener));
  });
  const baseUrl = `http://127.0.0.1:${server.address().port}`;

  try {
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
  } finally {
    await new Promise((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
    });
  }
});
