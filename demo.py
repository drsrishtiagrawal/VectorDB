from vectordb import VectorDB

db = VectorDB(dim=3)
db.insert("cat", [0.9, 0.1, 0.0], {"type": "animal"})
db.insert("dog", [0.8, 0.2, 0.1], {"type": "animal"})
db.insert("car", [0.0, 0.1, 0.9], {"type": "vehicle"})

print("All:", db.search([1, 0, 0], k=3))
print("Animals only:", db.search([0, 0, 1], k=3, where={"type": "animal"}))
assert db.search([1, 0, 0], k=1)[0][0] == "cat"
assert db.search([0, 0, 1], k=1)[0][0] == "car"
print("OK")
