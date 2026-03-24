"""
Recommendation ranking is performed locally in this module.

Why merge sort:
- It guarantees O(n log n) worst-case behavior.
- It is stable, so when two items have the same score the previous ordering is preserved.
- It is simple to reason about when score weights change.

How the score works:
- community_score gives more weight to explicit recommendations than to raw views.
- affinity_score measures how much a movie matches the active user's recent history and favorite genres.
- source_score distinguishes whether the candidate came from a strongly related source
  (for example, a movie related to something the user recently watched) or from a weaker source
  such as genre discovery.

If the product needs a different behavior later, only compute_ranked_candidates needs to change.
For example, to prioritize community opinion even more than personal taste, increase the multiplier
used in community_score and the merge sort will keep producing a deterministic ordering.
"""


def community_score(stats: dict):
    return (
        stats.get("recommend_count", 0) * 6
        - stats.get("not_recommend_count", 0) * 4
        + stats.get("viewed_count", 0) * 2
    )


def affinity_score(candidate_genre_ids: list[int], genre_weights: dict[int, int], favorite_genre_ids: set[int]):
    genre_overlap_score = sum(genre_weights.get(genre_id, 0) for genre_id in candidate_genre_ids)
    favorite_bonus = sum(2 for genre_id in candidate_genre_ids if genre_id in favorite_genre_ids)
    return genre_overlap_score + favorite_bonus


def rank_movie(movie: dict):
    stats = movie.get("community_stats", {})
    return (
        movie.get("score", 0),
        stats.get("recommend_count", 0),
        stats.get("viewed_count", 0),
        movie.get("vote_average") or 0,
        -(movie.get("id") or 0),
    )


def merge_sort_movies(movies: list[dict]):
    if len(movies) <= 1:
        return movies

    middle = len(movies) // 2
    left = merge_sort_movies(movies[:middle])
    right = merge_sort_movies(movies[middle:])
    return _merge(left, right)


def _merge(left: list[dict], right: list[dict]):
    result = []
    left_index = 0
    right_index = 0

    while left_index < len(left) and right_index < len(right):
        if rank_movie(left[left_index]) >= rank_movie(right[right_index]):
            result.append(left[left_index])
            left_index += 1
        else:
            result.append(right[right_index])
            right_index += 1

    result.extend(left[left_index:])
    result.extend(right[right_index:])
    return result


def compute_ranked_candidates(
    candidates: list[dict],
    genre_weights: dict[int, int],
    favorite_genre_ids: set[int],
):
    for candidate in candidates:
        candidate["score"] = (
            candidate.get("source_score", 0)
            + community_score(candidate.get("community_stats", {}))
            + affinity_score(candidate.get("genre_ids", []), genre_weights, favorite_genre_ids)
        )
    return merge_sort_movies(candidates)
