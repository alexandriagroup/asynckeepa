import time
import os

import numpy as np
import pytest

import asynckeepa
import datetime

import asyncio

is_matplotlib = True
try:
    import matplotlib
except ModuleNotFoundError:
    is_matplotlib = False

# slow down number of offers for testing
asynckeepa.interface.REQLIM = 2

try:
    path = os.path.dirname(os.path.realpath(__file__))
    keyfile = os.path.join(path, 'key')
    weak_keyfile = os.path.join(path, 'weak_key')
except Exception:
    keyfile = '/home/alex/books/keepa/tests/key'
    weak_keyfile = '/home/alex/books/keepa/tests/weak_key'

if os.path.isfile(keyfile):
    with open(keyfile) as f:
        TESTINGKEY = f.read()
    with open(weak_keyfile) as f:
        WEAKTESTINGKEY = f.read()
else:
    # from travis-ci or appveyor
    TESTINGKEY = os.environ.get('KEEPAKEY')
    WEAKTESTINGKEY = os.environ.get('WEAKKEEPAKEY')


# this key returns "payment required"
DEADKEY = '8ueigrvvnsp5too0atlb5f11veinerkud47p686ekr7vgr9qtj1t1tle15fffkkm'


# harry potter book ISBN
PRODUCT_ASIN = '0439064872'

# ASINs of a bunch of chairs
# categories = API.search_for_categories('chairs')
# asins = []
# for category in categories:
#     asins.extend(API.best_sellers_query(category))
# PRODUCT_ASINS = asins[:40]

PRODUCT_ASINS = ['B00IAPNWG6', 'B01CUJMSB2', 'B01CUJMRLI',
                 'B00BMPT7CE', 'B00IAPNWE8', 'B0127O51FK',
                 'B01CUJMT3E', 'B01A5ZIXKI', 'B00KQPBF1W',
                 'B000J3UZ58', 'B00196LLDO', 'B002VWK2EE',
                 'B00E2I3BPM', 'B004FRSUO2', 'B00CM1TJ1G',
                 'B00VS4514C', 'B075G1B1PK', 'B00R9EAH8U',
                 'B004L2JKTU', 'B008SIDW2E', 'B078XL8CCW',
                 'B000VXII46', 'B07D1CJ8CK', 'B07B5HZ7D9',
                 'B002VWK2EO', 'B000VXII5A', 'B004N1AA5W',
                 'B002VWKP3W', 'B00CM9OM0G', 'B002VWKP4G',
                 'B004N18JDC', 'B07MDHF4CP', 'B002VWKP3C',
                 'B07FTVSNL2', 'B002VWKP5A', 'B002O0LBFW',
                 'B07BM1Q64Q', 'B004N18JM8', 'B004N1AA02',
                 'B002VWK2EY']


# open connection to keepa
API = asynckeepa.Keepa(TESTINGKEY)
asyncio.run(API.connect())
assert API.tokens_left
assert API.time_to_refill >= 0


@pytest.mark.asyncio
async def test_invalidkey():
    with pytest.raises(Exception):
        asynckeepa.Api('thisisnotavalidkey')


@pytest.mark.asyncio
async def test_deadkey():
    with pytest.raises(Exception):
        asynckeepa.Api(DEADKEY)


@pytest.mark.skipif(WEAKTESTINGKEY is None, reason="No weak key given")
@pytest.mark.asyncio
async def test_throttling():
    api = asynckeepa.Keepa(WEAKTESTINGKEY)
    await api.connect()
    asynckeepa.interface.REQLIM = 20

    # exaust tokens
    while api.tokens_left > 0:
        await api.query(PRODUCT_ASINS[:5])

    # this must trigger a wait...
    t_start = time.time()
    await api.query(PRODUCT_ASINS)
    assert (time.time() - t_start) > 1
    asynckeepa.interface.REQLIM = 2


@pytest.mark.asyncio
async def test_productquery_nohistory():
    pre_update_tokens = API.tokens_left
    request = await API.query(PRODUCT_ASIN, history=False)
    assert API.tokens_left != pre_update_tokens

    product = request[0]
    assert product['csv'] is None
    assert product['asin'] == PRODUCT_ASIN


@pytest.mark.asyncio
async def test_not_an_asin():
    with pytest.raises(Exception):
        asins = ['0000000000', '000000000x']
        await API.query(asins)


@pytest.mark.asyncio
async def test_isbn13():
    isbn13 = '9780786222728'
    await API.query(isbn13, product_code_is_asin=False, history=False)


@pytest.mark.asyncio
async def test_productquery_update():
    request = await API.query(PRODUCT_ASIN, update=0, stats=90, rating=True)
    product = request[0]

    # should be live data
    now = datetime.datetime.now()
    delta = now - product['data']['USED_time'][-1]
    assert delta.days <= 30

    # check for empty arrays
    history = product['data']
    for key in history:
        assert history[key].any()

        # should be a key pair
        if 'time' not in key:
            assert history[key].size == history[key + '_time'].size

    # check for stats
    assert 'stats' in product

    # no offers requested by default
    assert product['offers'] is None


@pytest.mark.asyncio
async def test_productquery_offers():
    request = await API.query(PRODUCT_ASIN, offers=20)
    product = request[0]

    offers = product['offers']
    for offer in offers:
        assert offer['lastSeen']
        assert not len(offer['offerCSV']) % 3

    # also test offer conversion
    offer = offers[1]
    times, prices = asynckeepa.convert_offer_history(offer['offerCSV'])
    assert times.dtype == datetime.datetime
    assert prices.dtype == np.double
    assert len(times)
    assert len(prices)


@pytest.mark.asyncio
async def test_productquery_offers_invalid():
    with pytest.raises(ValueError):
        await API.query(PRODUCT_ASIN, offers=2000)


@pytest.mark.asyncio
async def test_productquery_offers_multiple():
    products = await API.query(PRODUCT_ASINS)

    asins = np.unique([product['asin'] for product in products])
    assert len(asins) == len(PRODUCT_ASINS)
    assert np.in1d(asins, PRODUCT_ASINS).all()


@pytest.mark.asyncio
async def test_domain():
    request = await API.query(PRODUCT_ASIN, history=False, domain='DE')
    product = request[0]
    assert product['asin'] == PRODUCT_ASIN


@pytest.mark.asyncio
async def test_invalid_domain():
    with pytest.raises(ValueError):
        await API.query(PRODUCT_ASIN, history=False, domain='XX')


@pytest.mark.asyncio
async def test_bestsellers():
    category = '402333011'
    asins = await API.best_sellers_query(category)
    valid_asins = asynckeepa.format_items(asins)
    assert len(asins) == valid_asins.size


@pytest.mark.asyncio
async def test_categories():
    categories = await API.search_for_categories('chairs')
    catids = list(categories.keys())
    for catid in catids:
        assert 'chairs' in categories[catid]['name'].lower()


@pytest.mark.asyncio
async def test_categorylookup():
    categories = await API.category_lookup(0)
    for cat_id in categories:
        assert categories[cat_id]['name']


@pytest.mark.asyncio
async def test_invalid_category():
    with pytest.raises(Exception):
        await API.category_lookup(-1)


@pytest.mark.asyncio
async def test_stock():
    request = await API.query(PRODUCT_ASIN, history=False, stock=True,
                        offers=20)

    # all live offers must have stock
    product = request[0]
    assert product['offersSuccessful']
    live = product['liveOffersOrder']
    for offer in product['offers']:
        if offer['offerId'] in live:
            assert offer['stockCSV'][-1]


def test_keepatime():
    keepa_st_ordinal = datetime.datetime(2011, 1, 1)
    assert keepa_st_ordinal == asynckeepa.keepa_minutes_to_time(0)
    assert asynckeepa.keepa_minutes_to_time(0, to_datetime=False)


@pytest.mark.asyncio
@pytest.mark.skipif(not is_matplotlib, reason="matplotlib not found")
async def test_plotting():
    request = await API.query(PRODUCT_ASIN, history=True)
    product = request[0]
    asynckeepa.plot_product(product, show=False)


@pytest.mark.asyncio
@pytest.mark.skipif(not is_matplotlib, reason="matplotlib not found")
async def test_empty():
    import matplotlib.pyplot as plt
    plt.close('all')
    products = await API.query(['B01I6KT07E', 'B01G5BJHVK', 'B017LJP1MO'])
    with pytest.raises(Exception):
        asynckeepa.plot_product(products[0], show=False)


@pytest.mark.asyncio
async def test_seller_query():
    seller_id = 'A2L77EE7U53NWQ'
    seller_info = await API.seller_query(seller_id)
    assert len(seller_info['sellers']) == 1
    assert seller_id in seller_info['sellers']


@pytest.mark.asyncio
async def test_seller_query_list():
    seller_id = ['A2L77EE7U53NWQ', 'AMMEOJ0MXANX1']
    seller_info = await API.seller_query(seller_id)
    assert len(seller_info['sellers']) == len(seller_id)
    assert set(seller_info['sellers']).issubset(seller_id)


@pytest.mark.asyncio
async def test_seller_query_long_list():
    seller_id = ['A2L77EE7U53NWQ']*200
    with pytest.raises(RuntimeError):
        await API.seller_query(seller_id)
