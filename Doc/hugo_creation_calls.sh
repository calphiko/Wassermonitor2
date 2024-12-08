

rm -rf hugo/
mkdir hugo

hugo new site hugo/ --force

git init hugo

cd hugo

#### FOR NEW BUILDS
git submodule add https://github.com/McShelby/hugo-theme-relearn.git themes/hugo-theme-relearn

#sed -i "/baseURL = 'http:\/\/example.org\/'/c baseURL = 'https:\/\/mondor.pakleds-patentoffice.de\/' " config.toml
#sed -i "/title = 'My New Hugo Site'/c title = 'Mondor Documentation'" config.toml

cp ../template/hugo.toml ./
#cp ../template/hugo.toml
#cp ../template/themes/hugo-theme-learn/layouts/partials/logo.html themes/hugo-theme-learn/layouts/partials/

#echo "theme = 'hugo-theme-learn'" >> config.toml

#cp -r ../template/static/css/ static/
#cp -r ../template/static/images/ static/

#cp -r template/* hugo/ 
cp -r ../content/* content/

cd ..

#python3 disable_home_button.py

cd hugo
#touch layouts/home.html
#hugo new content content/home.md
hugo

cd ..

