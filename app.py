"Main Flask app for RUL package"

from flask import Flask, render_template, request
from flask import send_file, session
from flask import url_for, redirect
from flask_cors import cross_origin
from werkzeug.utils import secure_filename

import os
import pandas as pd

from rul.pipeline.batch_prediction import start_batch_prediction
from rul.pipeline.training_pipeline import start_training_pipeline


# APP configuration and global variables
app = Flask(__name__,template_folder="templates",static_folder="static")
UPLOAD_FOLDER = 'static\\files\\'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30 * 1000 * 1000
app.secret_key ="xy"


@app.route('/', methods=['GET'])  
@cross_origin()
def homePage():
    """
    Route for homepage
    ------------------------------------------------------------
    input: 
    - `None`
    ------------------------------------------------------------
    return: `render_template("home.html")`
    """
    return render_template("home.html")


@app.route('/batch_prediction', methods=['POST', 'GET'])
def run_batch_prediction():
    """
    Route for Batch Prediction
    -------------------------------------------------------------------------------
    input: 
    - `None`
    -------------------------------------------------------------------------------
    return: `render_template("output.html")` else `render_template("warning.html")`
    """

    if request.method == "POST":
        try:
            # Running batch prediction on base dataset
            run_batch_prediction.prediction_file_path = start_batch_prediction(input_file_path='rul.csv')

            prediction_df = pd.read_csv(run_batch_prediction.prediction_file_path).head(1000)

            return render_template("output.html", tables=[prediction_df.to_html(classes="dataframe", header=True)], titles=prediction_df.columns.values)

        except Exception as e:
            message = "Batch Prediction Failed! Issue occurred at our end!"
        return render_template("warning.html", message=message)
    

@app.route('/download_batch_prediction') 
def download_batch_prediction():
    """
    Function to download prediction from `run_batch_prediction`
    ------------------------------------------------------------
    input: 
    - `None`
    ------------------------------------------------------------
    return: `prediction.csv`
    """
    return send_file(run_batch_prediction.prediction_file_path,
        mimetype='text/csv',
        download_name='prediction.csv',
        as_attachment=True
    )


@app.route('/uploader', methods=['POST', 'GET']) 
def uploader():
    """
    Uploads custom csv dataset for batch prediction
    ------------------------------------------------------------
    input: 
    - `None`
    ------------------------------------------------------------
    return: `redirect(url_for("custom_batch_prediction"))`
    """

    if request.method == "POST":
        # accessing uploaded file name
        uploaded_file = request.files['file']

        # extracting uploaded file name
        data_filename  = secure_filename(uploaded_file.filename)

        # flask upload file 
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        uploaded_file.save(os.path.join(app.config["UPLOAD_FOLDER"], data_filename))
        print(os.path.join(app.config["UPLOAD_FOLDER"], data_filename))

        # storing uploaded file path in flask session
        session["uploaded_file_path"] = os.path.join(app.config["UPLOAD_FOLDER"], data_filename)

        return redirect(url_for("custom_batch_prediction"))
    

@app.route('/upload_form', methods=['POST', 'GET'])
def upload_form():
    """
    Route for Upload form
    ------------------------------------------------------------
    input: 
    - `None`
    ------------------------------------------------------------
    return: `render_template("uploadForm.html")`
    """
    return render_template("uploadForm.html")


@app.route('/custom_batch_prediction', methods=['POST', 'GET'])
def custom_batch_prediction():
    """
    Route for Custom Batch Prediction
    ------------------------------------------------------------
    input: 
    - `None`
    ------------------------------------------------------------
    return: `render_template("customOutput.html")` else `render_template("warning.html")`
    """

    try:
        uploaded_file_path = session.get("uploaded_file_path", None)

        # Renaming uploaded file to fit it in prediction file format
        rename_as = "rul.csv"
        try:
            os.rename(UPLOAD_FOLDER + os.path.basename(uploaded_file_path), UPLOAD_FOLDER + rename_as)
        except WindowsError:
            os.remove(os.path.join(UPLOAD_FOLDER,rename_as))
            os.rename(UPLOAD_FOLDER + os.path.basename(uploaded_file_path), UPLOAD_FOLDER + rename_as)
            
        renamed_uploaded_file_path = os.path.join(UPLOAD_FOLDER, rename_as)

        # Performing batch prediction for custom dataset
        custom_batch_prediction.prediction_file_path = start_batch_prediction(input_file_path=renamed_uploaded_file_path)

        custom_prediction_df = pd.read_csv(custom_batch_prediction.prediction_file_path).head(1000)

        return render_template("customOutput.html", tables=[custom_prediction_df.to_html(classes="dataframe", header=True)], titles=custom_prediction_df.columns.values)

    except Exception as e:
        message = "Correct format file not provided! Please provide file in csv format with appropriate structure"
        return render_template("warning.html", message=message)
    

@app.route('/download_custom_batch_prediction') 
def download_custom_batch_prediction():
    """
    Function to download prediction from `custom_batch_prediction`
    ------------------------------------------------------------
    input: 
    - `None`
    ------------------------------------------------------------
    return: `prediction.csv`
    """
    return send_file(custom_batch_prediction.prediction_file_path,
        mimetype='text/csv',
        download_name='prediction.csv',
        as_attachment=True
    )


@app.route('/retrain', methods=['POST', 'GET'])
def retrain():
    """
    Function to perform retraining
    ------------------------------------------------------------
    input: 
    - `None`
    ------------------------------------------------------------
    return: `render_template("trainingreport.html")`
    """

    try:
        start_training_pipeline()
        message = "Current trained model is better than previous model! Saving the current model!"
    except Exception as e:
        message = "Current trained model is not better than previous model"
    
    return render_template("trainingreport.html", message=message)





if __name__ == '__main__':
    app.run(debug=True)