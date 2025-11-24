import python_weather


async def get_todays_temp(city="London"):
    """Gets the overall temperature for today

    Parameters
    ----------
    city : str
        The city to get weather data from. (Default: "London")

    Returns
    -------
    int:
        The average temperature for the day
    None:
        This is returned as an error instead of throwing an exception
    """

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


async def get_upcomming_temps(city="London"):
    """Gets the overall temperature for the next 3 days.

    Parameters
    ----------
    city : str
        The city to get weather data from. (Default: "London")

    Returns
    -------
    int list:
        A list of average temperatures the next 3 days
    None:
        This is returned as an error instead of throwing an exception
    """
    try:
        client = python_weather.Client()
        weather = await client.get(city)
        print("weather data recceived:" + str(weather))
        await client.close()
        ret = []
        for daily in weather:
            ret.append(daily.temperature)
        return ret
    except TypeError:
        print('Given city was nil or not a string. Using default vlaue: "London"')
        await client.close()
        return await get_upcomming_temps(city="London")
    except Exception as e:
        print("unexpected exception " + str(e))
        await client.close()
        return None
