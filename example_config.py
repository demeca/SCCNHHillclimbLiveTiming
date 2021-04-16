config = {
    "eventPath" : './Events',
    #"eventNumber" : '1',
    "outDir" : './HTML',
}
config["AWSCommand"] = f'aws s3 sync {config.get("outDir")} s3://bucketname --acl public-read --metadata-directive REPLACE --cache-control max-age=0'

