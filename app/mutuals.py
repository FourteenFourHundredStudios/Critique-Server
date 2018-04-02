

def getMutuals(username):
    return [
        { 
            "$match" : {
                "username" : username
            }
        }, 
        { 
            "$project" : {
                "_id" : 0.0, 
                "followed" : "$following", 
                "username" : "$username"
            }
        }, 
        { 
            "$lookup" : {
                "from" : "users", 
                "localField" : "followed", 
                "foreignField" : "username", 
                "as" : "value"
            }
        }, 
        { 
            "$project" : {
                "followed" : "$followed", 
                "username" : "$username", 
                "following" : "$value.following"
            }
        }, 
        { 
            "$project" : {
                "followed" : "$followed", 
                "isMutual" : {
                    "$map" : {
                        "input" : "$following", 
                        "as" : "a", 
                        "in" : {
                            "$in" : [
                                "$username", 
                                "$$a"
                            ]
                        }
                    }
                }
            }
        }, 
        { 
            "$project" : {
                "mutuals" : {
                    "$map" : {
                        "input" : {
                            "$zip" : {
                                "inputs" : [
                                    "$followed", 
                                    "$isMutual"
                                ]
                            }
                        }, 
                        "as" : "el", 
                        "in" : {
                            "username" : {
                                "$arrayElemAt" : [
                                    "$$el", 
                                    0.0
                                ]
                            }, 
                            "isMutual" : {
                                "$arrayElemAt" : [
                                    "$$el", 
                                    1.0
                                ]
                            }
                        }
                    }
                }
            }
        }
    ]
