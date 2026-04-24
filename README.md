# envchain

> A CLI tool for managing and chaining environment variable profiles across local, staging, and production contexts.

---

## Installation

```bash
pip install envchain
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envchain
```

---

## Usage

Define your environment profiles in a `.envchain.toml` file at the root of your project:

```toml
[profiles.local]
DATABASE_URL = "postgres://localhost:5432/mydb"
DEBUG = "true"

[profiles.production]
DATABASE_URL = "postgres://prod-host:5432/mydb"
DEBUG = "false"
```

Then run a command with a specific profile:

```bash
envchain run --profile local python app.py
```

Chain multiple profiles together (later profiles override earlier ones):

```bash
envchain run --profile base --profile staging python app.py
```

Export a profile to your current shell session:

```bash
eval $(envchain export --profile local)
```

List all available profiles:

```bash
envchain list
```

---

## License

This project is licensed under the [MIT License](LICENSE).