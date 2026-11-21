import React, { useRef, useState } from "react";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const MIN_PASSWORD_LENGTH = 12;

async function imageAsBase64(file) {
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return btoa(binary);
}

async function readError(response) {
  const payload = await response.json().catch(() => ({}));
  return payload.error || `Request failed (${response.status}).`;
}

export default function App() {
  const [mode, setMode] = useState("encode");
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [recoveredMessage, setRecoveredMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const inputRef = useRef(null);

  function clearResults() {
    setError("");
    setNotice("");
    setRecoveredMessage("");
  }

  function handleModeChange(nextMode) {
    setMode(nextMode);
    setFile(null);
    setPassword("");
    setMessage("");
    clearResults();
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleFileChange(event) {
    const selected = event.target.files?.[0] || null;
    setFile(selected);
    clearResults();
    if (selected && (selected.type !== "image/png" || selected.size > MAX_IMAGE_BYTES)) {
      setError(selected.size > MAX_IMAGE_BYTES
        ? "Choose a PNG image no larger than 5 MB."
        : "Only PNG images are supported.");
    }
  }

  async function submit(event) {
    event.preventDefault();
    clearResults();
    if (!file) {
      setError("Choose a PNG image first.");
      return;
    }
    if (file.type !== "image/png" || file.size > MAX_IMAGE_BYTES) {
      setError("Choose a PNG image no larger than 5 MB.");
      return;
    }
    if (!password) {
      setError("Enter your password.");
      return;
    }
    if (mode === "encode" && [...password].length < MIN_PASSWORD_LENGTH) {
      setError(`New passwords must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    if (mode === "encode" && !message.trim()) {
      setError("Enter a message to hide.");
      return;
    }

    setBusy(true);
    try {
      const payload = {
        image: await imageAsBase64(file),
        password,
      };
      const endpoint = mode === "encode" ? "/api/encode" : "/api/decode";
      if (mode === "encode") payload.message = message;

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        cache: "no-store",
        credentials: "omit",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(await readError(response));

      if (mode === "encode") {
        const output = await response.blob();
        const objectUrl = URL.createObjectURL(output);
        const link = document.createElement("a");
        link.href = objectUrl;
        link.download = "stego-image.png";
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
        setNotice("Encrypted PNG created and downloaded.");
        setMessage("");
      } else {
        const result = await response.json();
        setRecoveredMessage(result.message);
        setNotice("Message authenticated and recovered.");
      }

      setPassword("");
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The request failed.");
    } finally {
      setBusy(false);
    }
  }

  function clearAll() {
    setFile(null);
    setMessage("");
    setPassword("");
    clearResults();
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Secure Image Steganography home">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>Pixel Vault</span>
        </a>
        <span className="privacy-chip"><span /> No file storage</span>
      </header>

      <section className="hero">
        <p className="eyebrow">PRIVATE BY DESIGN</p>
        <h1>Messages, tucked<br />out of sight.</h1>
        <p className="hero-copy">
          Encrypt a text message and embed it in a PNG, or recover a message
          with its password.
        </p>
      </section>

      <section className="workspace" aria-label="Message tools">
        <div className="mode-switch" role="tablist" aria-label="Choose an action">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "encode"}
            className={mode === "encode" ? "mode active" : "mode"}
            onClick={() => handleModeChange("encode")}
          >
            Hide a message
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "decode"}
            className={mode === "decode" ? "mode active" : "mode"}
            onClick={() => handleModeChange("decode")}
          >
            Reveal a message
          </button>
        </div>

        <form className="form-card" onSubmit={submit}>
          <label className="field-label" htmlFor="image">
            {mode === "encode" ? "Cover image" : "Image with a hidden message"}
          </label>
          <label className={file ? "dropzone selected" : "dropzone"} htmlFor="image">
            <input
              ref={inputRef}
              id="image"
              type="file"
              accept="image/png,.png"
              onChange={handleFileChange}
              aria-describedby="image-help"
            />
            <span className="upload-icon" aria-hidden="true">↑</span>
            <span className="upload-title">{file ? file.name : "Choose a PNG image"}</span>
            <span className="upload-help" id="image-help">
              {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : "PNG only · up to 5 MB"}
            </span>
          </label>

          {mode === "encode" && (
            <div className="field-group">
              <label className="field-label" htmlFor="message">Message</label>
              <textarea
                id="message"
                rows="4"
                maxLength="1000000"
                placeholder="Write the text you want to hide..."
                value={message}
                onChange={(event) => setMessage(event.target.value)}
              />
              <span className="field-hint">Up to 1 MB of UTF-8 text. Avoid putting sensitive text in shared-device browser sessions.</span>
            </div>
          )}

          <div className="field-group">
            <label className="field-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete={mode === "encode" ? "new-password" : "current-password"}
              minLength={mode === "encode" ? MIN_PASSWORD_LENGTH : undefined}
              maxLength="1024"
              placeholder={mode === "encode" ? "Use a strong, unique password" : "Enter the message password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <span className="field-hint">
              {mode === "encode"
                ? `Use at least ${MIN_PASSWORD_LENGTH} characters. The same password is required to recover the message.`
                : "Previously encoded messages with shorter passwords can still be recovered."}
            </span>
          </div>

          {error && <p className="feedback error" role="alert">{error}</p>}
          {notice && <p className="feedback success" role="status">{notice}</p>}

          <button className="primary-button" type="submit" disabled={busy}>
            {busy ? "Processing in memory..." : mode === "encode" ? "Encrypt and hide" : "Authenticate and reveal"}
          </button>
          <button className="clear-button" type="button" onClick={clearAll} disabled={busy}>
            Clear this session
          </button>
        </form>

        {recoveredMessage && (
          <section className="result-card" aria-label="Recovered message">
            <div className="result-heading">
              <h2>Recovered message</h2>
              <button type="button" onClick={() => setRecoveredMessage("")}>Clear</button>
            </div>
            <pre>{recoveredMessage}</pre>
          </section>
        )}
      </section>

      <aside className="privacy-note">
        <strong>What happens to your data?</strong>
        <p>
          This app does not intentionally save images, messages, or passwords.
          The API processes bounded requests in memory, sends the result, and
          drops request references. Your hosting provider may retain operational
          metadata, and garbage-collected runtimes cannot guarantee immediate
          physical memory erasure. Avoid using this service for high-risk secrets.
        </p>
      </aside>

      <footer>LSB embedding can be detected and may be destroyed by image edits or recompression.</footer>
    </main>
  );
}
