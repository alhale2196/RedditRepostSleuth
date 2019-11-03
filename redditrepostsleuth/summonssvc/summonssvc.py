import threading
import time
# TODO - Mega hackery, figure this out.
import sys
sys.path.append('./')
from redditrepostsleuth.common.config import config
from redditrepostsleuth.core.db import db_engine
from redditrepostsleuth.core.db import SqlAlchemyUnitOfWorkManager
from redditrepostsleuth.common.util.helpers import get_reddit_instance
from redditrepostsleuth.summonssvc.summonsmonitor import SummonsMonitor



if __name__ == '__main__':
    uowm = SqlAlchemyUnitOfWorkManager(db_engine)
    summons = SummonsMonitor(get_reddit_instance(), uowm)
    threading.Thread(target=summons.monitor_for_mentions, name='pushshift_summons').start()
    threading.Thread(target=summons.monitor_for_summons_pushshift, name='pushshift_summons').start()
    threading.Thread(target=summons.monitor_for_summons, name='praw_summons', args=(config.subreddit_summons,)).start()
    threading.Thread(target=summons.monitor_for_summons, name='praw_summons_all').start()

    while True:
        time.sleep(10)