

def getMutuals(username):
    return     [
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
                "score" : "$value.score", 
                "following" : "$value.following"
            }
        }, 
        { 
            "$project" : {
                "followed" : "$followed", 
                "score" : "$score", 
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
                                    "$isMutual", 
                                    "$score"
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
                            }, 
                            "score" : {
                                "$arrayElemAt" : [
                                    "$$el", 
                                    2.0
                                ]
                            }
                        }
                    }
                }
            }
        }
    ]
