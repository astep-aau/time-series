from typing import List, Optional, cast

import python_weather


async def get_todays_temp(city) -> Optional[int]:
    try:
        client = python_weather.Client()
        weather = await client.get(city)
        print("weather data recceived:" + str(weather))
        await client.close()
        return weather.temperature
    except TypeError:
        await client.close()
        return None
    except Exception as e:
        print("unexpected exception " + str(e))
        await client.close()
        return None


async def get_upcoming_temps(city) -> Optional[List[int]]:
    try:
        client = python_weather.Client()
        weather = await client.get(city)
        print("weather data recceived:" + str(weather))
        await client.close()
        ret = []
        weather = cast(python_weather.forecast.Forecast, weather)
        for daily in weather.daily_forecasts:
            ret.append(daily.temperature)
        return ret
    except TypeError:
        await client.close()
        return None
    except Exception as e:
        print("unexpected exception " + str(e))
        await client.close()
        return None
