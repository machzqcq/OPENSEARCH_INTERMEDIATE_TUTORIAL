# Generic Ingest & Search Application - Quick Reference

## 🚀 One-Command Deployment

```bash
docker-compose up -d --build
```

Access at: http://localhost:3000

## 🔑 Demo Credentials

- Admin: `admin` / `admin123`
- User: `user` / `user123`

## 📊 Supported File Formats

- ✅ CSV (Comma-separated values)
- ✅ XLSX (Excel spreadsheets)
- ✅ JSONL (JSON Lines)

## 🔍 Search Types

1. **Search-as-you-type**: Real-time prefix matching
2. **Semantic**: KNN vector similarity search
3. **Hybrid**: Combined keyword + semantic

## 🎯 Embedding Models

| Model | Dimensions | Speed | Quality |
|-------|------------|-------|---------|
| all-MiniLM-L6-v2 | 384 | ⚡⚡⚡ | ⭐⭐ |
| all-mpnet-base-v2 | 768 | ⚡⚡ | ⭐⭐⭐ |

## 🛠️ Common Commands

```bash
# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Clean slate
docker-compose down -v

# Check health
curl http://localhost:8000/health
```

## 📞 Service Ports

- Frontend: 3000
- Backend API: 8000
- OpenSearch: 9200
- Redis: 6379

## ⚠️ Troubleshooting

**OpenSearch won't start?**
```bash
sudo sysctl -w vm.max_map_count=262144
```

**Can't connect?**
- Check Docker memory (min 4GB)
- Wait for health checks
- View logs: `docker-compose logs`

## 📚 More Info

See [README.md](README.md) for full documentation.
