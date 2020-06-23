import json

from falcon import Response, Request, HTTPBadRequest, HTTPServiceUnavailable

from redditrepostsleuth.core.db.uow.unitofworkmanager import UnitOfWorkManager
from redditrepostsleuth.core.duplicateimageservice import DuplicateImageService
from redditrepostsleuth.core.exception import NoIndexException
from redditrepostsleuth.core.jsonencoders import ImageRepostWrapperEncoder
from redditrepostsleuth.core.logging import log


class ImageSearch:
    def __init__(self, image_svc: DuplicateImageService, uowm: UnitOfWorkManager):
        self.image_svc = image_svc
        self.uowm = uowm

    def on_get(self, req: Request, resp: Response):
        target_annoy = req.get_param_as_float('pre_filter', None)
        target_hamming = req.get_param_as_int('post_filter', None)
        same_sub = req.get_param_as_bool('same_sub', False)
        only_older = req.get_param_as_bool('only_older', False)
        date_cutoff = req.get_param_as_int('date_cutoff', None)
        meme_filter = req.get_param_as_bool('meme_filter', False)
        post_id = req.get_param('post_id', required=True)
        filter_dead_matches = req.get_param_as_bool('filter_dead_matches', False)

        with self.uowm.start() as uow:
            post = uow.posts.get_by_post_id(post_id)

        if not post:
            raise HTTPBadRequest("No Post Found", "We were unable to find a post with the provided ID")

        try:
            search_results = self.image_svc.check_duplicates_wrapped(
                post,
                target_annoy_distance=target_annoy,
                target_hamming_distance=target_hamming,
                meme_filter=meme_filter,
                same_sub=same_sub,
                date_cutoff=date_cutoff,
                only_older_matches=only_older,
                filter_dead_matches=filter_dead_matches,
                max_matches=500,
                max_depth=-1,
                source='api'
            )
        except NoIndexException:
            log.error('No available index for image repost check.  Trying again later')
            raise HTTPServiceUnavailable('Search API is not available.' 'The search API is current not available')

        resp.body = json.dumps(search_results, cls=ImageRepostWrapperEncoder)