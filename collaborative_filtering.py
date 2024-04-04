import mysql.connector
from collections import defaultdict
from math import sqrt

class CollaborativeFilteringRecommender:
    def __init__(self, user_item_ratings):
        self.user_item_ratings = user_item_ratings
        self.user_similarity = {}

    def train(self):
        # Calculate user similarity matrix
        for user1 in self.user_item_ratings:
            for user2 in self.user_item_ratings:
                if user1 != user2:
                    self.user_similarity.setdefault(user1, {})[user2] = self.calculate_similarity(user1, user2)

    def calculate_similarity(self, user1, user2):
        # Calculate cosine similarity between two users
        common_items = set(self.user_item_ratings[user1].keys()) & set(self.user_item_ratings[user2].keys())
        if len(common_items) == 0:
            return 0.0

        numerator = sum(self.user_item_ratings[user1][item] * self.user_item_ratings[user2][item] for item in common_items)
        denominator1 = sqrt(sum(pow(self.user_item_ratings[user1][item], 2) for item in common_items))
        denominator2 = sqrt(sum(pow(self.user_item_ratings[user2][item], 2) for item in common_items))
        return numerator / (denominator1 * denominator2)

    def predict_rating(self, user_id, item_id):
        # Predict rating for a given user and item
        numerator = 0.0
        denominator = 0.0
        for other_user in self.user_item_ratings:
            if other_user != user_id and item_id in self.user_item_ratings[other_user]:
                similarity = self.user_similarity[user_id].get(other_user, 0)
                numerator += similarity * self.user_item_ratings[other_user][item_id]
                denominator += abs(similarity)
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def get_recommendations(self, user_id, top_n=10):
        # Generate top-n recommendations for a given user
        recommendations = defaultdict(float)
        for other_user in self.user_item_ratings:
            if other_user != user_id:
                for item_id in self.user_item_ratings[other_user]:
                    if item_id not in self.user_item_ratings[user_id] or self.user_item_ratings[user_id][item_id] == 0:
                        recommendations[item_id] += self.predict_rating(user_id, item_id)

        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return sorted_recommendations

# Connect to MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="virtual_library"
)

# Fetch user-item ratings from user_likes table
user_item_ratings = defaultdict(dict)
cursor = conn.cursor()
cursor.execute("SELECT user_id, learning_resource_id FROM user_likes")
for row in cursor.fetchall():
    user_id, item_id = row
    user_item_ratings[user_id][str(item_id)] = 1  # Assuming user liked the resource
cursor.close()
conn.close()

# Create and train the recommender
recommender = CollaborativeFilteringRecommender(user_item_ratings)
recommender.train()

# Example: Get recommendations for a specific user
user_id = 2  # Example user ID
recommendations = recommender.get_recommendations(user_id)
print(recommendations)
