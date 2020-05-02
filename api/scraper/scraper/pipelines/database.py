class SaveToDbPipeline:
    def process_item(self, item, spider):
        try:
            item.save()
            print("Added %s" % item["name"])
        except:
            print("Could not add %s" % item["name"])
        return item
