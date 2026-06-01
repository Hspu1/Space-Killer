@profile_get_router.get(
    path="/get",
    dependencies=[
        Depends(rate_limiter(limit=3, period=60, burst=5, scope="profile_get"))
    ],
)
