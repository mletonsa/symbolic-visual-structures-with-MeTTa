"""
simple_blend.py

A teaching example, deliberately separate from the project's real pipeline.
Companion to simple_encoder.py.

simple_encoder.py shows concepts being built upward from adjacency. This file
shows the step after that: taking two concepts the system already has and
combining them into one it does not, which is what concept blending is for.

The demonstration uses three one-dimensional tasks:

    task A   fill rightward from a 1
    task B   fill leftward from a 1
    task C   fill the gap between two 1s

A and B are learned from their own examples. C is never learned. It is
produced by blending the concepts learned from A and B, and then checked
against C's examples, which the blend has never seen.

Two things are stipulated rather than discovered, and both are the same
simplification the real pipeline makes today (see docs/decisions.md D7):
  - the shape of a candidate concept is fixed in advance (a reach relation to
    some cell, plus that cell's colour)
  - anti-unification aligns atoms by position

Run:
    python docs/examples/simple_blend.py
"""

from __future__ import annotations


# --------------------------------------------------------------------------
# Facts about a row
# --------------------------------------------------------------------------

def facts(row: str, name: str) -> list:
    """Each cell's input colour, and which cells are at or to the left and at
    or to the right of which. Reach is inclusive, so a cell reaches itself."""
    n = len(row)
    out = [("colorIn", f"{name}{i}", "one" if ch == "1" else "zero")
           for i, ch in enumerate(row)]
    for i in range(n):
        for j in range(n):
            if j <= i:
                out.append(("atOrLeft", f"{name}{j}", f"{name}{i}"))
            if j >= i:
                out.append(("atOrRight", f"{name}{j}", f"{name}{i}"))
    return out


# --------------------------------------------------------------------------
# Anti-unification: what two structures have in common
# --------------------------------------------------------------------------

def antiunify(p: list, q: list) -> list:
    """Positionally aligned. Terms that agree survive. Terms that differ become
    a variable, and the same differing pair always becomes the same variable,
    which is how agreement between two slots is preserved."""
    table, out, n = {}, [], [0]

    def term(a, b):
        if a == b:
            return a
        if (a, b) not in table:
            n[0] += 1
            table[(a, b)] = f"$v{n[0]}"
        return table[(a, b)]

    for fa, fb in zip(p, q):
        if fa[0] != fb[0]:
            continue                      # unalignable predicates drop out
        out.append(tuple([fa[0]] + [term(x, y) for x, y in zip(fa[1:], fb[1:])]))
    return out


# --------------------------------------------------------------------------
# Matching a concept against a row
# --------------------------------------------------------------------------

def holds(concept: list, fs: list, self_id: str) -> bool:
    def step(i, b):
        if i == len(concept):
            return True
        p = concept[i]
        for f in fs:
            if f[0] != p[0] or len(f) != len(p):
                continue
            nb, ok = dict(b), True
            for pa, fa in zip(p[1:], f[1:]):
                if pa == "$self":
                    if fa != self_id:
                        ok = False
                        break
                elif pa.startswith("$"):
                    if pa in nb and nb[pa] != fa:
                        ok = False
                        break
                    nb[pa] = fa
                elif pa != fa:
                    ok = False
                    break
            if ok and step(i + 1, nb):
                return True
        return False
    return step(0, {})


def apply_concept(concept: list, row: str) -> str:
    fs = facts(row, "c")
    return "".join("1" if holds(concept, fs, f"c{i}") else "0"
                   for i in range(len(row)))


def reproduces(concept: list, task: list) -> bool:
    return all(apply_concept(concept, i) == o for i, o in task)


# --------------------------------------------------------------------------
# Learning a concept from a task
# --------------------------------------------------------------------------

def instance(row: str, out: str, i: int, anchor: str, name: str):
    """One concrete reason cell i became 1: some cell holding a 1 that reaches
    it under `anchor`. Returns None when there is no such cell."""
    fs = facts(row, name)
    reach = {(a, b) for p, a, b in fs if p == anchor}
    ones = {a for p, a, v in fs if p == "colorIn" and v == "one"}
    for w in sorted(ones):
        if (w, f"{name}{i}") in reach:
            return [(anchor, w, "$self"), ("colorIn", w, "one")]
    return None


def learn(task: list, anchor: str):
    """Anti-unify the first two instances found under this anchor."""
    found = []
    for k, (inp, out) in enumerate(task):
        for i, ch in enumerate(out):
            if ch == "1":
                ins = instance(inp, out, i, anchor, f"t{k}_")
                if ins:
                    found.append(ins)
                    break
        if len(found) == 2:
            break
    return antiunify(found[0], found[1]) if len(found) == 2 else None


def show(concept) -> str:
    return " ".join("(" + " ".join(a) + ")" for a in concept)


def rename(concept: list, tag: str) -> list:
    """Give a concept's variables their own namespace.

    Both concepts are learned independently and both happen to call their
    variable `$v1`, but those name two different cells. Combining them without
    renaming would silently force the two to be the same cell. `$self` is
    left alone, because there the two concepts really are talking about the
    same thing: the cell whose output we are deciding."""
    return [tuple([a[0]] + [x if x == "$self" or not x.startswith("$")
                            else f"${tag}{x[1:]}" for x in a[1:]])
            for a in concept]


# --------------------------------------------------------------------------

TASK_A = [("10000", "11111"), ("00100", "00111")]          # fill rightward
TASK_B = [("00001", "11111"), ("00100", "11100")]          # fill leftward
TASK_C = [("10100", "11100"), ("01010", "01110"),
          ("01001", "01111")]                              # fill the gap

ANCHORS = ("atOrLeft", "atOrRight")


def learn_task(label, task):
    print(f"\n{label}")
    for inp, out in task:
        print(f"    {inp}  ->  {out}")
    kept = None
    for anchor in ANCHORS:
        c = learn(task, anchor)
        if c is None:
            print(f"  {anchor:<10} no instances")
            continue
        ok = reproduces(c, task)
        print(f"  {anchor:<10} {show(c):<46} "
              f"{'reproduces the task' if ok else 'does not fit, discarded'}")
        if ok:
            kept = c
    return kept


def main():
    print("=" * 72)
    print("STEP 1  learn a concept from each of two tasks")
    print("=" * 72)
    A = learn_task("task A, fill rightward from a 1", TASK_A)
    B = learn_task("task B, fill leftward from a 1", TASK_B)

    print("\n" + "=" * 72)
    print("STEP 2  what the two concepts have in common")
    print("=" * 72)
    G = antiunify(A, B)
    print(f"  concept A      {show(A)}")
    print(f"  concept B      {show(B)}")
    print(f"  generic space  {show(G)}")
    print("\n  The reach atoms use different predicates, so they do not align")
    print("  and drop out. What survives is 'somewhere there is a cell holding")
    print("  a 1', which is the whole of what A and B agree on.")

    print("\n" + "=" * 72)
    print("STEP 3  project both concepts back into one blend")
    print("=" * 72)
    selective = rename(A, "a") + rename(B, "b")
    merged = [(A[0][0], "$w", "$self"), (B[0][0], "$w", "$self"),
              ("colorIn", "$w", "one")]
    print("  Both concepts call their variable $v1, but those are two")
    print("  different cells, so they are renamed apart first. $self stays")
    print("  shared: there the two concepts really do mean the same cell.")
    print()
    print(f"  keeping the two roles apart:  {show(selective)}")
    print(f"  merging them into one cell:   {show(merged)}")

    print("\n" + "=" * 72)
    print("STEP 4  test on task C, which nothing here has ever seen")
    print("=" * 72)
    print(f"  {'input':<9}{'A alone':<11}{'B alone':<11}{'blend':<11}"
          f"{'merged':<11}{'wanted':<9}")
    print("  " + "-" * 62)
    for inp, want in TASK_C:
        print(f"  {inp:<9}{apply_concept(A, inp):<11}{apply_concept(B, inp):<11}"
              f"{apply_concept(selective, inp):<11}"
              f"{apply_concept(merged, inp):<11}{want:<9}")

    print()
    for label, c in (("concept A alone", A), ("concept B alone", B),
                     ("blend, roles kept apart", selective),
                     ("blend, roles merged", merged)):
        print(f"  {label:<26} solves task C: {reproduces(c, TASK_C)}")


if __name__ == "__main__":
    main()
