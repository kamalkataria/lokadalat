outstanding=0
uaint=0
total=outstanding+uaint
compr=0
wavedfrompr=0
wavedfromint=0
tokenmoney=0
rest=0
outstanding=int(input("total outstanding:"))
uaint=int(input("unapplied int"))
total=outstanding+uaint
compr=int(input("compromise amount:"))
tokenmoney=int(input("token money"))
rest=compr-tokenmoney
if(compr>outstanding):
    wavedfrompr=0
    wavedfromint=total-compr
else:
    wavedfrompr=outstanding-compr
    wavedfromint=uaint
print("Outstanding:"+str(outstanding))
print("Total:"+str(total))
print("Unapplied Int:"+str(uaint))
print("Compromise:"+str(compr))
print("Outstanding:"+str(outstanding))
print("Waived from principle:"+str(wavedfrompr))
print("Waived from int:"+str(wavedfromint))
print("Token:"+str(tokenmoney))
print("Rest:"+str(rest))



