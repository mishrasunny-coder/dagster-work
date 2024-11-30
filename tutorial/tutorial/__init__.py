from dagster import Definitions, load_assets_from_modules, AssetSelection, define_asset_job, ScheduleDefinition, FilesystemIOManager

from . import assets

all_assets = load_assets_from_modules([assets])

hackernews_job = define_asset_job("hackernews_job", selection=AssetSelection.all())

hackernews_schedule = ScheduleDefinition(
    job = hackernews_job,
    cron_schedule= "0 * * * *"
)

io_manager = FilesystemIOManager(base_dir = "data")

defs = Definitions(
    assets=all_assets,
    jobs = [hackernews_job],
    schedules=[hackernews_schedule],
    resources={
        "io_manager": io_manager
    }
)
