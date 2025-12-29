def normalize(month, year):
    while month > 12:
        month -= 12
        year += 1
    while month < 1:
        month += 12
        year -= 1
    return month, year

print(f"13, 2025 -> {normalize(13, 2025)}")
print(f"0, 2025 -> {normalize(0, 2025)}")
print(f"25, 2025 -> {normalize(25, 2025)}")
print(f"-1, 2025 -> {normalize(-1, 2025)}")
