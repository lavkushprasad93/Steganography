from secure_steganography import decode_image, encode_image
from secure_steganography.interface import cli

PASSWORD = "correct horse battery staple"


def prompt_passwords(monkeypatch, *passwords):
    responses = iter(passwords)
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: next(responses))


def test_encode_cli_accepts_message_file_and_confirms_password(
    monkeypatch, tmp_path, cover_png
):
    cover = tmp_path / "cover.png"
    output = tmp_path / "encoded.png"
    message_file = tmp_path / "message.txt"
    message_file.write_text("hello, こんにちは 🌍", encoding="utf-8")
    cover.write_bytes(cover_png)
    prompt_passwords(monkeypatch, PASSWORD, PASSWORD)

    assert cli.main([
        "encode", str(cover), str(output), "--message-file", str(message_file)
    ]) == 0
    assert decode_image(output, PASSWORD) == "hello, こんにちは 🌍"


def test_encode_cli_rejects_mismatched_password_confirmation(
    monkeypatch, tmp_path, cover_png, capsys
):
    cover = tmp_path / "cover.png"
    output = tmp_path / "encoded.png"
    cover.write_bytes(cover_png)
    prompt_passwords(monkeypatch, PASSWORD, "different")

    assert cli.main(["encode", str(cover), str(output), "--message", "secret"]) == 2
    assert not output.exists()
    assert "Passwords do not match" in capsys.readouterr().err


def test_decode_cli_writes_utf8_and_requires_force_for_existing_output(
    monkeypatch, tmp_path, cover_png, capsys
):
    cover = tmp_path / "cover.png"
    encoded = tmp_path / "encoded.png"
    recovered = tmp_path / "recovered.txt"
    cover.write_bytes(cover_png)
    encode_image(cover, encoded, "hello, こんにちは 🌍", PASSWORD)
    recovered.write_text("keep this file", encoding="utf-8")

    prompt_passwords(monkeypatch, PASSWORD)
    assert cli.main(["decode", str(encoded), "--output", str(recovered)]) == 2
    assert recovered.read_text(encoding="utf-8") == "keep this file"
    assert "already exists" in capsys.readouterr().err

    prompt_passwords(monkeypatch, PASSWORD)
    assert cli.main([
        "decode", str(encoded), "--output", str(recovered), "--force"
    ]) == 0
    assert recovered.read_text(encoding="utf-8") == "hello, こんにちは 🌍"


def test_message_file_requires_utf8(monkeypatch, tmp_path, cover_png, capsys):
    cover = tmp_path / "cover.png"
    output = tmp_path / "encoded.png"
    message_file = tmp_path / "message.txt"
    cover.write_bytes(cover_png)
    message_file.write_bytes(b"\xff")
    prompt_passwords(monkeypatch, PASSWORD, PASSWORD)

    assert cli.main([
        "encode", str(cover), str(output), "--message-file", str(message_file)
    ]) == 2
    assert not output.exists()
    assert "valid UTF-8" in capsys.readouterr().err


def test_capacity_cli_uses_exact_maximum_wording(tmp_path, cover_png, capsys):
    cover = tmp_path / "cover.png"
    cover.write_bytes(cover_png)

    assert cli.main(["capacity", str(cover)]) == 0
    output = capsys.readouterr().out
    assert "Maximum plaintext capacity:" in output
    assert "Approximate" not in output
