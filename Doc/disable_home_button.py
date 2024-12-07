file_path = "hugo/themes/hugo-theme-learn/layouts/partials/menu.html"

modify_lines = [
    '<section id="homelinks">',
    '</section>'
]

with open (file_path, 'r') as f :
    lines = [line.rstrip() for line in f]
m = 0
i = 1
for l in range(len(lines)):
    #print (l)
    if modify_lines[0] in lines[l]:
        l_m = f"<!--  {lines[l]}" 
        print (f"{i} modify: {lines[l]} to  {l_m}")
        lines[l] = l_m
        m = 1
    if modify_lines[1] in lines[l] and m ==1:
        l_m = f"{lines[l]} -->"
        print (f"{i} modify: {lines[l]} to  {l_m}")
        lines[l] = l_m
        m = 0
    i+=1

with open (file_path, 'w') as f:
    f.writelines(lines)
