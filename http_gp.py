import requests

url = "https://chat.akash.network/api/chat"

headers = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/json",
    "origin": "https://chat.akash.network",
    "priority": "u=1, i",
    "referer": "https://chat.akash.network/",
    "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
}

cookies = {
    "_ga": "GA1.1.1253745525.1747739650",
    "_ga_LFRGN2J2RV": "GS2.1.s1747739650$o1$g0$t1747739650$j0$l0$h0",
    "cf_clearance": "QzF9mTXC0B9JeADpVK1NEHxaIhitXEl_cjn1SKhh97Q-1747740846-1.2.1.1-SODJPILydTweLgVvA9won4HBXE.bKnWAv1a76RPVRX7BbCk52MlO0xOWR8mJIifMcpLIxceVpdP7kExtHMLrnPRlfCithCVcp1gGcr6J1ABobkvP1_vNKZTsRv.I75qc9qCXRt6zGiTXyaw_7xMo4cabMEfTyfbqWJJ9D3ev4dhVk9P6F.ydqvF7EJcq7fyiFSwxqcpflobK.NMYRhM4LnkIUJ1IL9LzgcA_vcAIfR6Bdr4DSkzEZqSTc4UT4ge4csmMo_iX0A.33q7rnaJ4DB4ykDXYgyM610zOWZJ6S8S4umrOunfgvIWW53Ui5D_myfCxSsMX_Eh10GujtR3.dUCTOJpBaQBuDy935ZpSO_I",
    "session_token": "66509f7beb59a9e3aab2f6038739172d88536c971d78044aa4999c058160654d"
}

data = {
    "id": "x0qt4Nubn049Joib",
    "messages": [{"role": "user", "content": "你好"}],
    "model": "DeepSeek-R1",
    "system": "You are a helpful assistant with LaTeX support. Only use LaTeX formatting when responding to mathematical questions or when mathematical expressions are necessary to explain a concept.\n\nWhen mathematical content is needed, follow these guidelines:\n\n1. Use single dollar signs ($...$) for inline math: e.g., $x^2 + y^2 = r^2$\n2. Use double dollar signs ($$...$$) for block/display math:\n  $$\n  f(x) = \\int_{-\\infty}^{\\infty} \\hat{f}(\\xi)\\,e^{2 \\pi i \\xi x} \\,d\\xi\n  $$\n3. Format mathematical symbols, equations, and formulas using LaTeX syntax\n4. Use proper LaTeX commands for mathematical symbols (e.g., \\alpha, \\beta, \\sum, \\int)\n5. For complex equations, use environments like align*, matrix, cases when appropriate\n\nFor non-mathematical questions, respond naturally without using LaTeX formatting.",
    "temperature": 0.6,
    "topP": 0.95,
    "context": []
}

response = requests.post(url, headers=headers, cookies=cookies, json=data)

print("Status Code:", response.status_code)
print("Response:", response.text)