import requests
from PIL import Image
from io import BytesIO

url = "https://rendering.mcp.cimpress.com/v2/vp/preview?category=gal6&format=auto&quality=95&instructions_uri=https%3A%2F%2Finstructions.documents.cimpress.io%2Fv3%2Finstructions%3Apreview%3FignoreProjection%3Dtrue%26documentUri%3Dhttps%253A%252F%252Fdesign-specifications.design.vpsvc.com%252Fv2%252FrenderDocuments%252Fproducts%252FPRD-IYXT1T3V%252F44%252Ftemplates%252Fs41909c65-25ea-42da-8bea-57155639dec3%253Av3..8bc979ba-7a4b-4c3b-8274-97e7e733d94a%253Fculture%253Den-us%2526useFakeFamily%253Dfalse%2526requester%253Dgallery-content-query%2526optionSelections%25255BFinish%25255D%253DNone%2526optionSelections%25255BBacksides%25255D%253DBlank%2526optionSelections%25255BShape%25255D%253DStandard%2526optionSelections%25255BCorners%25255D%253DStandard%2BCorners%2526optionSelections%25255BThickness%25255D%253DStandard%2526optionSelections%25255BSubstrate%25255D%253DMatte%2526optionSelections%25255BProduct%2BOrientation%25255D%253DHorizontal%2526optionSelections%25255BConnected%2BCards%25255D%253DNone&merchant_metadata=s41909c65-25ea-42da-8bea-57155639dec3%3Av3..8bc979ba-7a4b-4c3b-8274-97e7e733d94a&scene=https%3A%2F%2Fscenes.documents.cimpress.io%2Fv3%2Fscenes%3Agenerate%3Fdata%3DlY%252FBboMwEET%252FZc4WggQk8Df0UKm5VTk4ZgVWwUb2oiRF%252FvcKg5pGvbSX1ezI83a84Gpa7iHrQynQk%252Bl6hizrg0AYHEMumFRHkIXAqMLHavB9IkiwNyNiFNDOMt3S29Cr1l1Xpd3g%252FCo8ZC7QpXlJU0EWVR4FlO0GSlZrAiurtyWYz1VkebHSJ%252B%252FaWSf6XhVNVjR6xKMvquxYJyfMl8BeMf0oOipmQhRb49TNspt9gHxfoAcXqIVkP5NAYOX51RmbDt4gkWdFldD3x7J%252F2s3%252BjbqRLG%252Bo%252Fd6LsXRyECDbPqGaLC9%252FoaL4Z7DKDse%252FBp%252FKfwfP8Rxj%252FAI%253D&width=412&showerr=true&bgcolor=f3f3f3"

response = requests.get(url)

if response.status_code == 200:
    image = Image.open(BytesIO(response.content))
    # Сохраняем изображение в формате JPEG
    image.save("photo.jpg", "JPEG")
    print("Изображение сохранено как photo.jpg")
else:
    print("Ошибка при загрузке изображения:", response.status_code)
