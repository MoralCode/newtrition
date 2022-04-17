COOKIES_FILE = "cookies.txt"
NN_BASE_URL = "https://www.rit.edu/fa/diningservices/netnutrition/1"
# https://www.rit.edu/fa/diningservices/netnutrition/1/NutritionDetail/ShowItemNutritionLabel

ARCHIVE_DB_CONNECTION_STR = "sqlite:///archive.db"
PROCESSING_BATCH_SIZE = 25


JSON_HEADERS = {
	"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
	"Referer": NN_BASE_URL,
	"User-Agent": "Newtrition bot https://github.com/MoralCode/newtrition"
}