#!/usr/bin/env bash
ps aux | grep rustc | grep -v grep | head -5
