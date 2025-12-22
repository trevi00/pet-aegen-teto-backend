#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug comment line breaking"""

comment = '츤데레같은 느낌! 수려한 외모에 도도하게 있을 것 같지만 반려자님께 항상 의지하고 있을 것 같아요!'
max_chars = 25

print(f'Total comment length: {len(comment)} characters')
print(f'Comment: "{comment}"')
print()

# Calculate lines
lines = []
for i in range(0, len(comment), max_chars):
    lines.append(comment[i:i + max_chars])

print(f'Number of lines: {len(lines)}')
print()

for i, line in enumerate(lines):
    print(f'Line {i}: "{line}" ({len(line)} chars)')
