from flask import g, jsonify, request

from server import app, sqldb
from server.auth import auth
from server.models import Degree, Major, School, SchoolMajorAccount


@app.route("/account/degrees", methods=["POST"])
@auth()
def add_degrees():
    json = request.get_json()
    add_schools_and_majors(g.account, json)
    return jsonify({"success": True})


@app.route("/account/degrees/delete", methods=["POST"])
@auth()
def delete_degrees():
    SchoolMajorAccount.query.filter_by(account_id=g.account.id).delete()
    sqldb.session.commit()
    return jsonify({"success": True})


def add_schools_and_majors(account, json_array):
    # Remove degrees in DB and replace with new ones (if any)
    SchoolMajorAccount.query.filter_by(account_id=account.id).delete()

    account_schools = []
    for json in json_array:
        school_name = json.get("school_name")
        school_code = json.get("school_code")
        degree_name = json.get("degree_name")
        degree_code = json.get("degree_code")
        majors = json.get("majors")
        expected_grad = json.get("expected_grad_term")

        if school_name is None:
            raise KeyError("school_name is missing")
        if school_code is None:
            raise KeyError("school_code is missing")
        if degree_name is None:
            raise KeyError("degree_name is missing")
        if degree_code is None:
            raise KeyError("degree_code is missing")
        if majors is None:
            raise KeyError("majors is missing")
        if expected_grad is None:
            raise KeyError("expected_grad_term is missing")

        school = School.query.filter_by(name=school_name, code=school_code).first()
        if school is None:
            school = School(name=school_name, code=school_code)
            sqldb.session.add(school)
            sqldb.session.commit()

        degree = Degree.query.filter_by(code=degree_code).first()
        if degree is None:
            degree = Degree(name=degree_name, code=degree_code, school_id=school.id)
            sqldb.session.add(degree)
            sqldb.session.commit()

        if majors:
            for mJSON in majors:
                major_name = mJSON.get("major_name")
                major_code = mJSON.get("major_code")

                if major_name is None:
                    raise KeyError("major_name is missing")
                if major_code is None:
                    raise KeyError("major_code is missing")

                major = Major.query.filter_by(code=major_code).first()
                if major is None:
                    major = Major(name=major_name, code=major_code, degree_code=degree_code)
                    sqldb.session.add(major)
                    sqldb.session.commit()

                asm = SchoolMajorAccount(
                    account_id=account.id,
                    school_id=school.id,
                    major=major.code,
                    expected_grad=expected_grad,
                )
                account_schools.append(asm)
        else:
            asm = SchoolMajorAccount(
                account_id=account.id, school_id=school.id, major=None, expected_grad=expected_grad
            )
            account_schools.append(asm)

    if account_schools:
        for asm in account_schools:
            sqldb.session.add(asm)
        sqldb.session.commit()
