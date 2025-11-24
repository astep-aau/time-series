from typing import List, Optional, cast

import python_weather


async def get_todays_temp(city="London") -> Optional[int]:
    try:
        client = python_weather.Client()
        weather = await client.get(city)
        print("weather data recceived:" + str(weather))
        await client.close()
        return weather.temperature
    except TypeError:
        print('Given city was nil or not a string. Using default vlaue: "London"')
        await client.close()
        return await get_todays_temp(city="London")
    except Exception as e:
        print("unexpected exception " + str(e))
        await client.close()
        return None


async def get_upcoming_temps(city="London") -> Optional[List[int]]:
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
        print('Given city was nil or not a string. Using default vlaue: "London"')
        await client.close()
        return await get_upcoming_temps(city="London")
    except Exception as e:
        print("unexpected exception " + str(e))
        await client.close()
        return None
