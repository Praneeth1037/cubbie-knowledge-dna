"""Academic source provenance and bounded priors. No fetching, commands or native tools."""
from urllib.parse import urlsplit

STATUSES={'connected','disconnected','unavailable','not_requested','no_matches'}
TYPES={'canvas_feedback','canvas_assignment','canvas_rubric','canvas_page','canvas_submission',
       'google_docs','google_drive','google_draft','gmail'}


def prepare(request, patterns, domain):
    connections=request.get('connections',{})
    if not isinstance(connections,dict):raise ValueError('connections must be an object')
    connections={key:connections.get(key,'not_requested') for key in ('canvas','google')}
    if any(not isinstance(v,str) or v not in STATUSES for v in connections.values()):
        raise ValueError('Unsupported connection status')
    sources=request.get('sources',[])
    if not isinstance(sources,list) or len(sources)>6:raise ValueError('Pass at most six compact sources')
    cleaned=[];ids=set();synthetic_values=set()
    for source in sources:
        if not isinstance(source,dict):raise ValueError('Each source must be an object')
        kind=source.get('source_type')
        if kind not in TYPES:raise ValueError('Unsupported source type')
        synthetic=source.get('synthetic',False)
        if type(synthetic) is not bool:raise ValueError('synthetic must be boolean')
        if synthetic and request.get('synthetic_mode') is not True:raise ValueError('Synthetic sources require explicit synthetic_mode')
        provider='canvas' if kind.startswith('canvas') else 'google'
        if not synthetic and (request.get('evidence_authorized') is not True or connections[provider]!='connected'):
            raise ValueError('Real academic sources require consent and an available connected account')
        item={}
        for field,limit in [('id',50),('title',100),('excerpt',240)]:
            value=source.get(field)
            if not isinstance(value,str) or not value.strip() or len(value)>limit:
                raise ValueError(f'Source {field} must be nonempty and at most {limit} characters')
            item[field]=value
        if item['id'] in ids:raise ValueError('Source IDs must be unique')
        ids.add(item['id'])
        url=source.get('url','')
        if not isinstance(url,str) or len(url)>240:raise ValueError('Source URL is too long')
        if url:
            parsed=urlsplit(url)
            if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Source URL must be HTTPS without credentials')
            # Retain stable provenance; never persist signed tokens or tracking parameters.
            url=parsed._replace(query='',fragment='').geturl()
        reference=source.get('reference','')
        if not isinstance(reference,str) or len(reference)>120:raise ValueError('Source reference is too long')
        if not url and not reference:raise ValueError('Each source needs a link or reference')
        evidence_type=source.get('evidence_type')
        if evidence_type not in {'direct','inferred'}:raise ValueError('evidence_type must be direct or inferred')
        supports=source.get('supports',[])
        if not isinstance(supports,list) or len(supports)>4 or any(h not in patterns or patterns[h]['domain']!=domain for h in supports):
            raise ValueError('Sources must support known hypotheses in this domain')
        item.update(source_type=kind,url=url,reference=reference,evidence_type=evidence_type,
                    supports=list(dict.fromkeys(supports)),synthetic=synthetic)
        synthetic_values.add(synthetic);cleaned.append(item)
    if len(synthetic_values)>1:raise ValueError('Keep synthetic fixtures separate from real academic evidence')
    return connections,cleaned


def prioritize(hypotheses,sources):
    for key,record in hypotheses.items():
        refs=[s['id'] for s in sources if key in s['supports']]
        record['source_support']=refs
        record['score']+=min(2,len(refs))
