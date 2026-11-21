"use strict";

const { promisify } = require("node:util");
const {
  createCipheriv,
  createDecipheriv,
  pbkdf2,
  randomBytes,
} = require("node:crypto");
const sharp = require("sharp");

const pbkdf2Async = promisify(pbkdf2);
const MAGIC = Buffer.from("STG2", "ascii");
const SALT_SIZE = 16;
const NONCE_SIZE = 12;
const TAG_SIZE = 16;
const ITERATIONS = 600_000;
const HEADER_SIZE = MAGIC.length + SALT_SIZE + NONCE_SIZE + 4;
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const MAX_IMAGE_PIXELS = 4_000_000;
const MAX_MESSAGE_BYTES = 1_000_000;
const MAX_PASSWORD_BYTES = 1024;
const MIN_PASSWORD_LENGTH = 12;

class SteganographyError extends Error {}

function assertPngBuffer(imageBuffer) {
  if (!Buffer.isBuffer(imageBuffer) || imageBuffer.length === 0) {
    throw new SteganographyError("Choose a non-empty PNG image.");
  }
  if (imageBuffer.length > MAX_IMAGE_BYTES) {
    throw new SteganographyError("Image exceeds the 5 MB upload limit.");
  }
}

function invalidImageError(error) {
  if (!(error instanceof Error)) throw error;
  return new SteganographyError("Input is not a valid PNG image.");
}

async function loadRgb(imageBuffer) {
  assertPngBuffer(imageBuffer);

  let metadata;
  try {
    metadata = await sharp(imageBuffer, {
      failOn: "error",
      limitInputPixels: MAX_IMAGE_PIXELS,
    }).metadata();
  } catch (error) {
    throw invalidImageError(error);
  }
  if (metadata.format !== "png") {
    throw new SteganographyError("Only PNG images are supported.");
  }
  if (!metadata.width || !metadata.height || metadata.width * metadata.height > MAX_IMAGE_PIXELS) {
    throw new SteganographyError("Image dimensions exceed the 4-megapixel limit.");
  }
  if (metadata.pages && metadata.pages > 1) {
    throw new SteganographyError("Animated PNG images are not supported.");
  }

  let decoded;
  try {
    decoded = await sharp(imageBuffer, {
      failOn: "error",
      limitInputPixels: MAX_IMAGE_PIXELS,
    })
      .toColourspace("srgb")
      .removeAlpha()
      .raw()
      .toBuffer({ resolveWithObject: true });
  } catch (error) {
    throw invalidImageError(error);
  }

  const { data, info } = decoded;
  if (info.channels !== 3) {
    throw new SteganographyError("Image could not be converted to RGB.");
  }
  return { data, width: info.width, height: info.height };
}

function maximumCiphertextBytes(channelCount) {
  return Math.max(0, Math.floor(channelCount / 8) - HEADER_SIZE);
}

function maximumPlaintextBytes(channelCount) {
  return Math.max(0, maximumCiphertextBytes(channelCount) - TAG_SIZE);
}

function getPasswordBytes(password, requireMinimum = false) {
  if (typeof password !== "string" || password.length === 0) {
    throw new SteganographyError("Password must not be empty.");
  }
  const passwordBytes = Buffer.from(password, "utf8");
  if (passwordBytes.length > MAX_PASSWORD_BYTES) {
    passwordBytes.fill(0);
    throw new SteganographyError("Password must be 1024 bytes or fewer.");
  }
  if (requireMinimum && [...password].length < MIN_PASSWORD_LENGTH) {
    passwordBytes.fill(0);
    throw new SteganographyError(
      `New passwords must be at least ${MIN_PASSWORD_LENGTH} characters.`,
    );
  }
  return passwordBytes;
}

function validateNewPassword(password) {
  getPasswordBytes(password, true).fill(0);
}

async function deriveKey(password, salt) {
  const passwordBytes = getPasswordBytes(password);
  try {
    return await pbkdf2Async(passwordBytes, salt, ITERATIONS, 32, "sha256");
  } finally {
    passwordBytes.fill(0);
  }
}

function embedPayload(channelData, payload) {
  let bitIndex = 0;
  for (const byte of payload) {
    for (let shift = 7; shift >= 0; shift -= 1) {
      channelData[bitIndex] = (channelData[bitIndex] & 0xfe) | ((byte >> shift) & 1);
      bitIndex += 1;
    }
  }
}

function readPayload(channelData, byteLength) {
  if (byteLength * 8 > channelData.length) {
    throw new SteganographyError("Image ended before the complete payload could be read.");
  }
  const output = Buffer.alloc(byteLength);
  for (let byteIndex = 0; byteIndex < byteLength; byteIndex += 1) {
    let value = 0;
    for (let bit = 0; bit < 8; bit += 1) {
      const channelIndex = byteIndex * 8 + bit;
      value = (value << 1) | (channelData[channelIndex] & 1);
    }
    output[byteIndex] = value;
  }
  return output;
}

async function encodePng(imageBuffer, message, password) {
  if (typeof message !== "string" || message.length === 0) {
    throw new SteganographyError("Message must not be empty.");
  }
  validateNewPassword(password);
  const plaintext = Buffer.from(message, "utf8");
  if (plaintext.length > MAX_MESSAGE_BYTES) {
    plaintext.fill(0);
    throw new SteganographyError("Message exceeds the 1 MB limit.");
  }

  let channelData;
  let key;
  try {
    const image = await loadRgb(imageBuffer);
    channelData = image.data;
    const ciphertextSize = plaintext.length + TAG_SIZE;
    if (ciphertextSize > maximumCiphertextBytes(channelData.length)) {
      throw new SteganographyError(
        `Message exceeds this image's capacity (${maximumPlaintextBytes(channelData.length)} bytes).`,
      );
    }

    const salt = randomBytes(SALT_SIZE);
    const nonce = randomBytes(NONCE_SIZE);
    const header = Buffer.alloc(HEADER_SIZE);
    let offset = 0;
    MAGIC.copy(header, offset);
    offset += MAGIC.length;
    salt.copy(header, offset);
    offset += SALT_SIZE;
    nonce.copy(header, offset);
    offset += NONCE_SIZE;
    header.writeUInt32BE(ciphertextSize, offset);

    key = await deriveKey(password, salt);
    const cipher = createCipheriv("aes-256-gcm", key, nonce);
    cipher.setAAD(header);
    const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final(), cipher.getAuthTag()]);
    const payload = Buffer.concat([header, encrypted]);
    embedPayload(channelData, payload);
    const encodedPng = await sharp(channelData, {
      raw: { width: image.width, height: image.height, channels: 3 },
    })
      .png()
      .toBuffer();
    if (encodedPng.length > MAX_IMAGE_BYTES) {
      encodedPng.fill(0);
      throw new SteganographyError("Encoded PNG exceeds the 5 MB limit.");
    }
    return encodedPng;
  } finally {
    plaintext.fill(0);
    if (key) key.fill(0);
    if (channelData) channelData.fill(0);
  }
}

async function decodePng(imageBuffer, password) {
  let channelData;
  let key;
  let encrypted;
  let plaintext;
  try {
    const image = await loadRgb(imageBuffer);
    channelData = image.data;
    if (channelData.length < HEADER_SIZE * 8) {
      throw new SteganographyError("Image is too small to contain a message.");
    }
    const header = readPayload(channelData, HEADER_SIZE);
    if (!header.subarray(0, MAGIC.length).equals(MAGIC)) {
      throw new SteganographyError("No supported hidden message was found in this image.");
    }
    const saltStart = MAGIC.length;
    const salt = header.subarray(saltStart, saltStart + SALT_SIZE);
    const nonceStart = saltStart + SALT_SIZE;
    const nonce = header.subarray(nonceStart, nonceStart + NONCE_SIZE);
    const ciphertextSize = header.readUInt32BE(nonceStart + NONCE_SIZE);
    if (ciphertextSize < TAG_SIZE || ciphertextSize > maximumCiphertextBytes(channelData.length)) {
      throw new SteganographyError("Invalid payload length; the image may be damaged.");
    }

    encrypted = readPayload(channelData.subarray(HEADER_SIZE * 8), ciphertextSize);
    key = await deriveKey(password, salt);
    const decipher = createDecipheriv("aes-256-gcm", key, nonce);
    decipher.setAAD(header);
    decipher.setAuthTag(encrypted.subarray(encrypted.length - TAG_SIZE));
    try {
      plaintext = Buffer.concat([
        decipher.update(encrypted.subarray(0, encrypted.length - TAG_SIZE)),
        decipher.final(),
      ]);
    } catch (error) {
      if (error instanceof Error) {
        throw new SteganographyError("Incorrect password or the embedded data has been modified.");
      }
      throw error;
    }

    try {
      return new TextDecoder("utf-8", { fatal: true }).decode(plaintext);
    } catch (error) {
      if (error instanceof TypeError) {
        throw new SteganographyError("The authenticated message is not valid UTF-8.");
      }
      throw error;
    }
  } finally {
    if (key) key.fill(0);
    if (encrypted) encrypted.fill(0);
    if (plaintext) plaintext.fill(0);
    if (channelData) channelData.fill(0);
  }
}

async function getCapacity(imageBuffer) {
  const image = await loadRgb(imageBuffer);
  try {
    return {
      width: image.width,
      height: image.height,
      maxMessageBytes: maximumPlaintextBytes(image.data.length),
    };
  } finally {
    image.data.fill(0);
  }
}

module.exports = {
  MAX_IMAGE_BYTES,
  MAX_MESSAGE_BYTES,
  MAX_PASSWORD_BYTES,
  MIN_PASSWORD_LENGTH,
  SteganographyError,
  decodePng,
  encodePng,
  getCapacity,
};
