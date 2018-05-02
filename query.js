// Stages that have been excluded from the aggregation pipeline query
__3tsoftwarelabs_disabled_aggregation_stages = [

	{
		// Stage 5 - excluded
		stage: 5,  source: {
			$project: {
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
		}
	},

	{
		// Stage 6 - excluded
		stage: 6,  source: {
			$project: {
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
	},
]

db.users.aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$match: {
			    "username" : "marc"
			}
		},

		// Stage 2
		{
			$project: {
			    "_id" : 0.0, 
			    "followed" : "$following", 
			    "username" : "$username"
			}
		},

		// Stage 3
		{
			$lookup: {
			    "from" : "users", 
			    "localField" : "followed", 
			    "foreignField" : "username", 
			    "as" : "value"
			}
		},

		// Stage 4
		{
			$project: {
			    "followed" : "$followed", 
			    "username" : "$username", 
			    "score" : "$value.score", 
			    "following" : "$value.following"
			}
		},

	]

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
