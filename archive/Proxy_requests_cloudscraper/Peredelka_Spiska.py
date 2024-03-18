proxy_list = ["rdZvZY:4hB2v9@193.124.190.63:9317",
"rdZvZY:4hB2v9@194.67.201.189:9874",
"rdZvZY:4hB2v9@194.67.202.219:9973",
"rdZvZY:4hB2v9@194.67.200.169:9485",
"rdZvZY:4hB2v9@194.67.202.109:9013",
"rdZvZY:4hB2v9@194.67.201.44:9798",
"rdZvZY:4hB2v9@194.67.201.206:9707",
"rdZvZY:4hB2v9@193.124.191.145:9587",
"rdZvZY:4hB2v9@194.67.201.205:9292",
"rdZvZY:4hB2v9@194.67.200.64:9821",
"QWyoUo:nRTyzY@194.67.202.181:9851",
"QWyoUo:nRTyzY@194.67.202.134:9450",
"QWyoUo:nRTyzY@194.67.202.205:9319",
"QWyoUo:nRTyzY@194.67.202.203:9417",
"QWyoUo:nRTyzY@194.67.202.108:9223",
"QWyoUo:nRTyzY@193.124.191.159:9233",
"QWyoUo:nRTyzY@194.67.202.29:9387",
"QWyoUo:nRTyzY@194.67.202.198:9839",
"QWyoUo:nRTyzY@194.67.201.2:9043",
"QWyoUo:nRTyzY@194.67.201.51:9636"]

converted_proxy_list = [(item.split('@')[1].split(':')[0], int(item.split('@')[1].split(':')[1]), item.split('@')[0].split(':')[0], item.split('@')[0].split(':')[1]) for item in proxy_list]

print(converted_proxy_list)
