// Verified entry runner for news-image-20261120 (Node 22+, stdlib only).
// Validates entry.png (magic signature, IHDR <=1024x1024, chunk walk through IEND,
// size <= 1,048,576 bytes) and writes it atomically to MAKEFUN_OUTPUT_DIR/entry.png
// (or /output/entry.png inside the grader container), printing JSON metadata + SHA-256.

import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const MAX_BYTES = 1_048_576;
const MAX_DIM = 1024;
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const IEND_TRAILER = Buffer.from([
  0x00, 0x00, 0x00, 0x00,
  0x49, 0x45, 0x4e, 0x44,
  0xae, 0x42, 0x60, 0x82,
]);

interface PngInfo {
  bytes: number;
  width: number;
  height: number;
  sha256: string;
}

function validatePng(buf: Buffer): PngInfo {
  if (buf.length === 0) {
    throw new Error('entry.png is empty');
  }
  if (buf.length > MAX_BYTES) {
    throw new Error(`entry.png exceeds ${MAX_BYTES} bytes (got ${buf.length})`);
  }
  if (buf.length < 33 || !buf.subarray(0, 8).equals(PNG_SIGNATURE)) {
    throw new Error('entry.png does not start with a valid PNG signature');
  }

  const ihdrLen = buf.readUInt32BE(8);
  const ihdrType = buf.subarray(12, 16).toString('ascii');
  if (ihdrType !== 'IHDR' || ihdrLen !== 13) {
    throw new Error(`Invalid PNG IHDR chunk: type=${ihdrType} len=${ihdrLen}`);
  }

  const width = buf.readUInt32BE(16);
  const height = buf.readUInt32BE(20);
  if (width < 1 || width > MAX_DIM || height < 1 || height > MAX_DIM) {
    throw new Error(`PNG dimensions ${width}x${height} outside 1..${MAX_DIM}`);
  }

  // Walk every chunk to guarantee structural integrity and an exact IEND terminator.
  let offset = 8;
  let sawIend = false;
  while (offset + 12 <= buf.length) {
    const chunkLen = buf.readUInt32BE(offset);
    const chunkType = buf.subarray(offset + 4, offset + 8).toString('ascii');
    const nextOffset = offset + 12 + chunkLen;
    if (nextOffset > buf.length) {
      throw new Error(`Truncated PNG chunk ${chunkType} at offset ${offset}`);
    }
    if (chunkType === 'IEND') {
      if (chunkLen !== 0 || nextOffset !== buf.length) {
        throw new Error('Invalid or trailing data after PNG IEND chunk');
      }
      if (!buf.subarray(offset, nextOffset).equals(IEND_TRAILER)) {
        throw new Error('PNG IEND trailer CRC mismatch');
      }
      sawIend = true;
      break;
    }
    offset = nextOffset;
  }

  if (!sawIend) {
    throw new Error('PNG file missing terminating IEND chunk');
  }

  const sha256 = createHash('sha256').update(buf).digest('hex');
  return { bytes: buf.length, width, height, sha256 };
}

function main(): void {
  const srcPath = fileURLToPath(new URL('./entry.png', import.meta.url));
  const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
  const destPath = join(outDir, 'entry.png');

  const pngBytes = readFileSync(srcPath);
  const info = validatePng(pngBytes);

  mkdirSync(dirname(destPath), { recursive: true });
  const tmpPath = join(dirname(destPath), `.entry.${process.pid}.tmp`);
  try {
    writeFileSync(tmpPath, pngBytes);
    renameSync(tmpPath, destPath);
  } catch (err) {
    rmSync(tmpPath, { force: true });
    throw err;
  }

  console.log(JSON.stringify(info));
}

main();
