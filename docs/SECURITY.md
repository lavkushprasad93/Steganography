# Security and data handling

- AES-GCM provides message confidentiality and integrity when the password is strong and the nonce is unique. The application generates a random salt and nonce for each encoding.
- New encodings require passwords with at least 12 Unicode characters. Existing images remain decodable with shorter passwords for compatibility; this minimum is a length policy, not a guarantee of password entropy.
- A wrong password or modified authenticated payload is rejected. Passwords are never stored in the image; losing one makes extraction impossible.
- Web requests are processed in bounded memory buffers. The application uses no database, upload directory, or content logging. The hosting provider may retain IP addresses, timestamps, or other operational metadata.
- Python and Node runtimes, image libraries, and operating systems may create internal copies. The application cannot guarantee immediate physical erasure from garbage-collected memory.
- The local CLI reads and writes files at the paths supplied by the user; its output PNG is intentionally persistent.
- PNG is required. Recompression, resizing, filtering, and screenshots may destroy embedded data.
- Basic LSB embedding is detectable by steganalysis and must not be described as undetectable or suitable for high-risk covert use.

Report project issues through the repository's issue tracker. Do not include passwords or private message contents in issue reports.
