import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from flask import request, jsonify
app = Flask(__name__)

# 프로젝트 루트 디렉토리
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# static 폴더의 경로 (정적 파일 디렉토리)
STATIC_FOLDER = os.path.join(PROJECT_ROOT, 'static')

# templates 폴더의 경로 (HTML 템플릿 디렉토리)
TEMPLATES_FOLDER = os.path.join(PROJECT_ROOT, 'templates')

# 파일 업로드를 저장할 폴더 설정
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 예시용 블로그 데이터
posts = []

# 필터 정의
def basename(value):
    return os.path.basename(value)

# Jinja2에 필터 추가
app.jinja_env.filters['basename'] = basename

# 정적 파일 서빙을 위한 엔드포인트 추가
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 검색 기능 추가
@app.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search_query', '').lower()

    # 게시물 제목, 해시태그, 게시물 내용에서 검색
    search_results = [post for post in posts if
                      search_query in post['title'].lower() or
                      any(search_query in tag.lower() for tag in post['hashtags']) or
                      search_query in post['content'].lower()]

    return render_template('search_results.html', search_query=search_query, search_results=search_results)

# 더 효율적인 검색 기능 추가
def search_posts(search_query):
    return [post for post in posts if
            search_query in post['title'].lower() or
            any(search_query in tag.lower() for tag in post['hashtags']) or
            search_query in post['content'].lower()]

# 홈 페이지에서 검색 기능 추가
@app.route('/', methods=['GET', 'POST'])
def home():
    search_query = request.form.get('search_query', '').lower()
    if search_query:
        search_results = search_posts(search_query)
        return render_template('index.html', posts=posts, search_results=search_results)
    else:
        return render_template('index.html', posts=posts)

@app.route('/search', methods=['POST'])
def search_posts():
    keyword = request.form.get('keyword')

    if not keyword:
        return jsonify({'error': '검색어를 입력하세요.'})

    matching_posts = []

    for post in posts:
        if keyword.lower() in post['title'].lower() or keyword.lower() in post['content'].lower() or keyword.lower() in post['hashtags']:
            matching_posts.append(post)

    return jsonify({'posts': matching_posts})

# 글 작성 페이지
@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        hashtags = request.form['hashtags'].split(',') if 'hashtags' in request.form else []  # 해시태그를 쉼표로 구분하여 리스트로 변환

        # 파일 업로드 처리
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename
            else:
                image_path = None
        else:
            image_path = None

        new_post = {'title': title, 'content': content, 'image_path': image_path, 'hashtags': hashtags}
        posts.append(new_post)
        return redirect(url_for('home'))
    return render_template('write.html')

if __name__ == '__main__':
    app.run(debug=True)

# 게시물 삭제
@app.route('/delete/<title>', methods=['GET'])
def delete(title):
    global posts
    posts = [post for post in posts if post['title'] != title]
    return redirect(url_for('home'))

def matches_search_query(post, search_query):
    return (
        search_query in post['title'].lower() or
        search_query in post['content'].lower() or
        any(search_query in tag.lower() for tag in post['hashtags'])
    )

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search_query', '').lower()

    # 검색 쿼리와 일치하는 게시물 필터링
    search_results = [post for post in posts if matches_search_query(post, search_query)]

    return render_template('search_results.html', search_query=search_query, search_results=search_results)