- [ ] Review current .env / .gitignore status
- [ ] Update .gitignore to ignore .env, local sqlite db, python caches, build artifacts, media/static uploads, and secrets
- [ ] Ensure settings.py reads env vars safely (SECRET_KEY via decouple, DATABASE_URL via dj_database_url)
- [ ] Add/adjust .env.example so contributors know required vars
- [ ] Optionally add runtime .env to Render/hosting configuration (not committed)

