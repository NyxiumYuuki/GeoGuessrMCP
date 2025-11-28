@mcp.tool()
async def analyze_recent_games(count: int = 10) -> dict:
    """
    Analyze recent games and provide statistics summary.
    Fetches recent games from the activity feed and calculates aggregate statistics.

    Args:
        count: Number of recent games to analyze (default: 10)
    """
    async with await get_async_session() as client:
        # Get activity feed
        feed_response = await client.get(
            f"{GEOGUESSR_BASE_URL}/v4/feed/private", params={"count": count * 2, "page": 0}
        )
        feed_response.raise_for_status()
        feed = feed_response.json()

        games_analyzed = []
        total_score = 0
        total_rounds = 0
        perfect_rounds = 0

        for entry in feed.get("entries", []):
            if entry.get("type") == "PlayedGame" and len(games_analyzed) < count:
                game_token = entry.get("payload", {}).get("gameToken")
                if game_token:
                    try:
                        game_response = await client.get(
                            f"{GEOGUESSR_BASE_URL}/v3/games/{game_token}"
                        )
                        if game_response.status_code == 200:
                            game = game_response.json()

                            game_info = {
                                "token": game_token,
                                "map": game.get("map", {}).get("name", "Unknown"),
                                "mode": game.get("type", "Unknown"),
                                "total_score": 0,
                                "rounds": [],
                            }

                            for round_data in game.get("player", {}).get("guesses", []):
                                round_score = round_data.get("roundScoreInPoints", 0)
                                game_info["total_score"] += round_score
                                game_info["rounds"].append(
                                    {
                                        "score": round_score,
                                        "distance": round_data.get("distanceInMeters", 0),
                                        "time": round_data.get("time", 0),
                                    }
                                )

                                total_rounds += 1
                                if round_score == 5000:
                                    perfect_rounds += 1

                            total_score += game_info["total_score"]
                            games_analyzed.append(game_info)
                    except Exception as e:
                        logger.warning(f"Failed to fetch game {game_token}: {e}")

        return {
            "games_analyzed": len(games_analyzed),
            "total_score": total_score,
            "average_score": total_score / len(games_analyzed) if games_analyzed else 0,
            "total_rounds": total_rounds,
            "perfect_rounds": perfect_rounds,
            "perfect_round_percentage": (
                (perfect_rounds / total_rounds * 100) if total_rounds > 0 else 0
            ),
            "games": games_analyzed,
        }


@mcp.tool()
async def get_performance_summary() -> dict:
    """
    Get a comprehensive performance summary combining profile stats,
    achievements, and season information.
    """
    async with await get_async_session() as client:
        results = {}

        # Get profile
        try:
            profile_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles")
            profile_response.raise_for_status()
            results["profile"] = profile_response.json()
        except Exception as e:
            results["profile_error"] = str(e)

        # Get stats
        try:
            stats_response = await client.get(f"{GEOGUESSR_BASE_URL}/v3/profiles/stats")
            stats_response.raise_for_status()
            results["stats"] = stats_response.json()
        except Exception as e:
            results["stats_error"] = str(e)

        # Get extended stats
        try:
            extended_response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/stats/me")
            extended_response.raise_for_status()
            results["extended_stats"] = extended_response.json()
        except Exception as e:
            results["extended_stats_error"] = str(e)

        # Get season stats
        try:
            season_response = await client.get(f"{GEOGUESSR_BASE_URL}/v4/seasons/active/stats")
            season_response.raise_for_status()
            results["current_season"] = season_response.json()
        except Exception as e:
            results["season_error"] = str(e)

        # Get achievements
        try:
            achievements_response = await client.get(
                f"{GEOGUESSR_BASE_URL}/v3/profiles/achievements"
            )
            achievements_response.raise_for_status()
            achievements = achievements_response.json()
            results["achievements_summary"] = {
                "total": len(achievements) if isinstance(achievements, list) else 0,
                "achievements": achievements,
            }
        except Exception as e:
            results["achievements_error"] = str(e)

        return results
