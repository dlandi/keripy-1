#!/bin/bash
# DoB26Fj4x9LboAFWJra17O
curl -s -X POST "http://localhost:5623/boot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"name\":\"delegate1\",\"passcode\":\"DoB2-6Fj4x-9Lbo-AFWJr-a17O\",\"salt\":\"0AMDEyMzQ1Njc4OWxtbm9wcQ\"}" | jq
curl -s -X POST "http://localhost:5723/boot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"name\":\"delegate2\",\"passcode\":\"DoB2-6Fj4x-9Lbo-AFWJr-a17O\", \"salt\":\"0AMDEyMzQ1Njc4OWdoaWpsaw\"}" | jq
curl -s -X POST "http://localhost:5823/boot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"name\":\"delegator1\",\"passcode\":\"DoB2-6Fj4x-9Lbo-AFWJr-a17O\", \"salt\":\"0AMDEyMzQ1Njc4OWdoaWpdo1\"}" | jq
curl -s -X POST "http://localhost:5923/boot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"name\":\"delegator2\",\"passcode\":\"DoB2-6Fj4x-9Lbo-AFWJr-a17O\", \"salt\":\"0AMDEyMzQ1Njc4OWdoaWpdo2\"}" | jq
sleep 2
curl -s -X PUT "http://localhost:5623/boot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"name\":\"delegate1\",\"passcode\":\"DoB2-6Fj4x-9Lbo-AFWJr-a17O\"}" | jq
curl -s -X PUT "http://localhost:5723/boot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"name\":\"delegate2\",\"passcode\":\"DoB2-6Fj4x-9Lbo-AFWJr-a17O\"}" | jq
curl -s -X PUT "http://localhost:5823/boot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"name\":\"delegator1\",\"passcode\":\"DoB2-6Fj4x-9Lbo-AFWJr-a17O\"}" | jq
curl -s -X PUT "http://localhost:5923/boot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"name\":\"delegator2\",\"passcode\":\"DoB2-6Fj4x-9Lbo-AFWJr-a17O\"}" | jq
sleep 2
curl -s -X POST "http://localhost:5623/ids/delegate1" -H "accept: */*" -H "Content-Type: application/json" -d "{\"transferable\":true,\"wits\":[\"BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\"],\"toad\":1,\"icount\":1,\"ncount\":1,\"isith\":1,\"nsith\":1}" | jq
curl -s -X POST "http://localhost:5723/ids/delegate2" -H "accept: */*" -H "Content-Type: application/json" -d "{\"transferable\":true,\"wits\":[\"BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\"],\"toad\":1,\"icount\":1,\"ncount\":1,\"isith\":1,\"nsith\":1}" | jq
curl -s -X POST "http://localhost:5823/ids/delegator1" -H "accept: */*" -H "Content-Type: application/json" -d "{\"transferable\":true,\"wits\":[\"BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\",\"BuyRFMideczFZoapylLIyCjSdhtqVb31wZkRKvPfNqkw\",\"Bgoq68HCmYNUDgOz4Skvlu306o_NY-NrYuKAVhk3Zh9c\"],\"toad\":2,\"icount\":1,\"ncount\":1,\"isith\":1,\"nsith\":1}" | jq
curl -s -X POST "http://localhost:5923/ids/delegator2" -H "accept: */*" -H "Content-Type: application/json" -d "{\"transferable\":true,\"wits\":[\"BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\",\"BuyRFMideczFZoapylLIyCjSdhtqVb31wZkRKvPfNqkw\",\"Bgoq68HCmYNUDgOz4Skvlu306o_NY-NrYuKAVhk3Zh9c\"],\"toad\":2,\"icount\":1,\"ncount\":1,\"isith\":1,\"nsith\":1}" | jq
sleep 3
curl -s -X POST "http://localhost:5623/oobi/delegate2" -H "accept: */*" -H "Content-Type: application/json" -d "{\"url\":\"http://127.0.0.1:5642/oobi/E64X4wS9Oaps6NtcsE_rgNoxxAT5QzdGfGyUKu1ecHgo/witness/BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\"}" | jq
curl -s -X POST "http://localhost:5723/oobi/delegate1" -H "accept: */*" -H "Content-Type: application/json" -d "{\"url\":\"http://127.0.0.1:5642/oobi/Eo6MekLECO_ZprzHwfi7wG2ubOt2DWKZQcMZvTbenBNU/witness/BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\"}" | jq
curl -s -X POST "http://localhost:5823/oobi/delegator2" -H "accept: */*" -H "Content-Type: application/json" -d "{\"url\":\"http://127.0.0.1:5642/oobi/EC1DxuYp8GgIDVQ2c8EYBaY1CwxozvQuqGxwppNVrapY/witness/BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\"}" | jq
curl -s -X POST "http://localhost:5923/oobi/delegator1" -H "accept: */*" -H "Content-Type: application/json" -d "{\"url\":\"http://127.0.0.1:5642/oobi/Ef9Bhn_LeAU3rq8Rf3XHi5C1XmNdIM5uxv2DwWQT6qd8/witness/BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\"}" | jq
# sleep 2
# curl -s -X POST "http://localhost:5823/groups/multisig/icp" -H "accept: */*" -H "Content-Type: application/json" -d "{\"delpre\":\"ED5IijFSuXv9ieknCduE_GXyX0h0o30bhtoemUO_wPwI\",\"aids\":[\"EozYHef4je02EkMOA1IKM65WkIdSjfrL7XWDk_JzJL9o\",\"E-4-PsMBN0YEKyTl3zL0zulWcBehdaaG6Go5cMc0BzQ8\"],\"transferable\":true,\"wits\":[\"BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\",\"BuyRFMideczFZoapylLIyCjSdhtqVb31wZkRKvPfNqkw\",\"Bgoq68HCmYNUDgOz4Skvlu306o_NY-NrYuKAVhk3Zh9c\"],\"toad\":3,\"isith\":2,\"nsith\":2}" | jq
# curl -s -X PUT "http://localhost:5923/groups/multisig/icp" -H "accept: */*" -H "Content-Type: application/json" -d "{\"delpre\":\"ED5IijFSuXv9ieknCduE_GXyX0h0o30bhtoemUO_wPwI\",\"aids\":[\"EozYHef4je02EkMOA1IKM65WkIdSjfrL7XWDk_JzJL9o\",\"E-4-PsMBN0YEKyTl3zL0zulWcBehdaaG6Go5cMc0BzQ8\"],\"transferable\":true,\"wits\":[\"BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo\",\"BuyRFMideczFZoapylLIyCjSdhtqVb31wZkRKvPfNqkw\",\"Bgoq68HCmYNUDgOz4Skvlu306o_NY-NrYuKAVhk3Zh9c\"],\"toad\":3,\"isith\":2,\"nsith\":2}" | jq
# sleep 2
# curl -s -X PUT "http://localhost:5823/ids/delegator/rot" -H "accept: */*" -H "Content-Type: application/json" -d "{\"data\":[{\"i\":\"EytoCy2sDJiusNU_wKZg8W_M5BZGfvWiPp_NwyHLgvBU\",\"s\":\"0\",\"d\":\"EytoCy2sDJiusNU_wKZg8W_M5BZGfvWiPp_NwyHLgvBU\"}]}" | jq

