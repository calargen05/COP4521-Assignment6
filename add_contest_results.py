from app import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

cur.executemany(
  """
  INSERT INTO BakingContestEntry
  (entry_id, user_id, item_name, num_excellent, num_ok, num_bad)
  VALUES (?, ?, ?, ?, ?, ?)
  """,
  [
    (1, 1, "Whoot Whoot Brownies", 1, 2, 4),
    (2, 2, "Cho Chip Cookies", 4, 1, 2),
    (3, 3, 'Cho Cake', 2, 4, 1),
    (4, 1, 'Sugar Cookies', 2, 2, 1)
  ]
)

conn.commit()
conn.close()
print('Static data inserted.')