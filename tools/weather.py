def get_weather(city: str) -> int:
    match city:
        case "New York":
            return 81
        case "Paris":
            return 60
        case _:
            return 75
