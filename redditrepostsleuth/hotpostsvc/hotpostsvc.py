# TODO - Mega hackery, figure this out.
import sys

from redditrepostsleuth.core.responsebuilder import ResponseBuilder

sys.path.append('./')
from redditrepostsleuth.common.logging import log


from redditrepostsleuth.core.db import db_engine
from redditrepostsleuth.core.db import SqlAlchemyUnitOfWorkManager
from redditrepostsleuth.common.util.helpers import get_reddit_instance
from redditrepostsleuth.core.duplicateimageservice import DuplicateImageService
from redditrepostsleuth.hotpostsvc.toppostmonitor import TopPostMonitor


if __name__ == '__main__':
    while True:
        uowm = SqlAlchemyUnitOfWorkManager(db_engine)
        dup = DuplicateImageService(uowm)
        response_builder = ResponseBuilder(uowm)
        top = TopPostMonitor(get_reddit_instance(), uowm, dup, response_builder)
        try:
            top.monitor()
        except Exception as e:
            log.exception('Service crashed', exc_info=True)
    #summons.monitor_for_summons()