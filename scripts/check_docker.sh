#!/usr/bin/env bash
which docker || echo "docker not in WSL path"
/mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe --version 2>/dev/null || echo "Docker Desktop not in default Program Files"
which rzup || echo "rzup not found"
curl -s --head https://risczero.com/install | head -5 || true
