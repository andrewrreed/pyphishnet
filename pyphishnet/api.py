import os
import requests
import datetime
import warnings
import pandas as pd
from .exceptions import ApiKeyError, ResponseError
from .util import parse_setlist_field


class PhishNetAPI:
    """
    An API wrapper for conveniently working with the Phish.net API
    """

    def __init__(self):
        """Initialize Phish.net API info and ensure API key variable set"""

        self._api_key = os.environ.get('PHISH_API_KEY')
        self._base_url = 'https://api.phish.net/v3'
        self._request_limit = 120
        if self._api_key is None:
            raise ApiKeyError('No API key found. Check your environment'
                              'variables and try again.')
        else:
            self.has_api_key = True

    # ------------- Response Error Handling Utilities -------------

    def _is_ok_response(self, response):
        """Check status code of API response"""

        if response.status_code == requests.codes.ok:
            pass
        else:
            response.raise_for_status()

    def _response_has_error(self, response):
        """Raise and format API response error"""

        json_response = response.json()
        if json_response.get('error_code') != 0:
            raise ResponseError(f"error code {json_response.get('error_code')}"
                                f": {json_response.get('error_message')}")

    # ------------- Query Parameter Utilities -------------

    def _add_api_key_to_query_params(self):
        """Initialize the API payload dictionary with API key"""

        payload = {}
        payload['apikey'] = self._api_key
        return payload

    def _mask_api_key_from_url(self, response, payload):
        """Anonomyze API key in response URL"""

        url = response.url.replace(payload['apikey'], '<<apikey>>')

        return url

    def _mask_api_key_from_query_string(self, response, payload, endpoint):
        """Anonomyze API key in response query string"""

        masked_url = response.url.replace(payload['apikey'], '<<apikey>>')
        query_string = masked_url.replace(endpoint, '')
        return query_string

    # ------------- URL Utilities -------------

    def _append_endpoint(self, url, endpoint):
        """Append an endpoint to a url"""

        return url + endpoint

    # ------------- Endpoint methods (GET, POST) -------------

    def get_all_venues(self):
        """
        Get all venues.

        Utilize the Phish.net /venues/all/ endpoint to pull all venue information.

        Returns:
            venues (dataframe) - a dataframe with all records of venue information from Phish.net
        """

        endpoint = '/venues/all'
        self.endpoint_ = self._append_endpoint(self._base_url, endpoint)

        payload = self._add_api_key_to_query_params()
        response = requests.request("GET", self.endpoint_, params=payload)

        self.url_ = self._mask_api_key_from_url(response, payload)
        self.query_string_ = self._mask_api_key_from_query_string(
            response, payload, self.endpoint_)

        self._is_ok_response(response)
        self._response_has_error(response)

        venues = pd.DataFrame(response.json().get(
            'response').get('data')).transpose()

        return venues

    def get_shows_by_year(self, year):
        """
        Get show by year.

        Given a year, utilize the Phish.net /shows/query/ endpoint to pull all shows by year and return as a dataframe.

        Args:
            year (int) - the year by which you want to query all_shows

        Returns:
            year_shows (dataframe) - a dataframe with records of show information for the input year

        """

        # define api endpoint
        endpoint = '/shows/query/'
        self.endpoint_ = self._append_endpoint(self._base_url, endpoint)

        # initialize dataframe to hold all shows
        all_shows = pd.DataFrame()

        # construct payload
        payload = self._add_api_key_to_query_params()
        payload['year'] = year
        payload['order'] = 'ASC'

        # request data
        response = requests.request("GET", self.endpoint_, params=payload)

        # save attributes
        self.url_ = self._mask_api_key_from_url(response, payload)
        self.query_string_ = self._mask_api_key_from_query_string(
            response, payload, self.endpoint_)

        # check response
        self._is_ok_response(response)
        self._response_has_error(response)

        # if that year has 300 shows, warn us because we may be missing data because of API cutoff
        if response.json().get('response').get('count') >= 300:
            warnings.warn(f'The year {year} has 300 or more shows, this API query is missing data.')

        # format data
        year_shows = pd.DataFrame(response.json().get(
            'response').get('data'))

        return year_shows



    def get_all_shows(self):
        """
        Get all shows.

        Utilize the Phish.net /shows/query/ endpoint to iteratively pull all shows by year and return as a dataframe

        Returns:
            all_shows (dataframe) - a dataframe with all records of show information from Phish.net

        """

        # initialize dataframe to hold all shows
        all_shows = pd.DataFrame()

        # query all shows by year
        for year in range(1983, datetime.datetime.now().year+1):

            # use get_shows_by_year() to query shows
            year_shows = self.get_shows_by_year(year)

            # append this years shows to master dataframe
            all_shows = pd.concat([all_shows, year_shows], ignore_index=True)

        return all_shows


    def get_setlist(self, showid):
        """
        Get a setlist.

        Given a showid, utilize the Phish.net /setlists/get/ endpoint to pull all show information and format into dataframe.

        Args:
            showid (int) - Phish.net showid

        Returns:
            setlist (dataframe) - a one record dataframe with all setlist info

        """

        # define api endpoint
        endpoint = '/setlists/get'
        self.endpoint_ = self._append_endpoint(self._base_url, endpoint)

        # construct payload
        payload = self._add_api_key_to_query_params()
        payload['showid'] = showid

        # request data
        response = requests.request("GET", self.endpoint_, params=payload)

        # save attributes
        self.url_ = self._mask_api_key_from_url(response, payload)
        self.query_string_ = self._mask_api_key_from_query_string(
            response, payload, self.endpoint_)

        # check response
        self._is_ok_response(response)
        self._response_has_error(response)

        # format data
        setlist = pd.DataFrame(response.json().get(
            'response').get('data'))

        return setlist
    
    def get_latest_setlist(self):
        """
        Get the latest setlist.

        Utilize the Phish.net /setlists/latest/ endpoint to pull all show information and format into dataframe.

        Returns:
            setlist (dataframe) - a one record dataframe with all setlist info

        """

        # define api endpoint
        endpoint = '/setlists/latest'
        self.endpoint_ = self._append_endpoint(self._base_url, endpoint)

        # construct payload
        payload = self._add_api_key_to_query_params()

        # request data
        response = requests.request("GET", self.endpoint_, params=payload)

        # save attributes
        self.url_ = self._mask_api_key_from_url(response, payload)
        self.query_string_ = self._mask_api_key_from_query_string(
            response, payload, self.endpoint_)

        # check response
        self._is_ok_response(response)
        self._response_has_error(response)

        # format data
        setlist = pd.DataFrame(response.json().get(
            'response').get('data'))

        return setlist

    def get_all_setlists(self, all_shows):
        """
        Get a all setlist data.

        Given an all_shows dataframe (the response from the get_all_shows() method), utilize the get_setlist() method to pull all setlist information and format into dataframe.

        NOTE: If a showid doesnt have a setlist populated, the record is skipped. Therefore, the output dataframe will NOT be identical to the input dataframe

        Args:
            all_shows (dataframe) - the response from the get_all_shows() method

        Returns:
            all_setlists (dataframe) - a dataframe with a setlist record for each showid in the input dataframe

        """

        all_setlists = pd.DataFrame()
        null_setlists = []

        for row in all_shows.iterrows():

            # request setlist data
            setlist = self.get_setlist(row[1].showid)

            if setlist.empty == True:
                # collect all showids that do not have a setlist populated on Phish.net
                null_setlists.append(row[1].showid)
            else:
                #parse the setlistdata field to a clean string and append
                setlist['setlistdata_clean'] = setlist['setlistdata'].apply(lambda x: parse_setlist_field(x))
                # append to storage dataframe
                all_setlists = all_setlists.append(setlist)

        if len(null_setlists) > 0:
            # alert the user of null setlists
            print(f'There are {len(null_setlists)} shows that do NOT have a setlist populated on Phish.net. These showids are save in the null_setlists attribute. ')
            # save shows with null setlists
            self.null_setlists = null_setlists
            
        return all_setlists
