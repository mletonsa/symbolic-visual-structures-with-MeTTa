# Symbolic–Visual Structures with MeTTa

This repository explores symbolic reasoning over visual structures using **MeTTa / Hyperon**, with experiments based on the **ARC (Abstraction and Reasoning Corpus)** dataset.

The code is designed to run inside a **Dockerized Hyperon environment** to ensure reproducibility and avoid local dependency issues.

---

## Requirements

- Git  
- Docker (tested with Docker Engine ≥ 24)

No local installation of Python, MeTTa, or Hyperon is required.

---

## Step 1: Clone repositories

From your working directory:

```
bash
git clone https://github.com/mletonsa/symbolic-visual-structures-with-MeTTa
git clone https://github.com/fchollet/ARC-AGI
```

You should have directory structure:

```
workspace/
├── symbolic-visual-structures-with-MeTTa/   ← this repository
└── ARC-AGI/                                 ← ARC dataset repository
```

---

## Step 2: Run the Hyperon Docker environment

From the parent directory (workspace/):

```
docker run -it --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  trueagi/hyperon:latest \
  bash
```
---

## Step 3: Run MeTTa experiments

Inside the container:

```
cd symbolic-visual-structures-with-MeTTa
metta src/main.metta
```
