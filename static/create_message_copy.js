$.fn.fileUploader = function (filesToUpload, sectionIdentifier) {
    var fileIdCounter = 0;

    this.closest(".files").change(function (evt) {
        var output = [];

        for (var i = 0; i < evt.target.files.length; i++) {
            fileIdCounter++;
            var file = evt.target.files[i];
            var fileId = sectionIdentifier + fileIdCounter;

            filesToUpload.push({
                id: fileId,
                file: file
            });

            var removeLink = "<a class=\"removeFile\" href=\"#\" data-fileid=\"" + fileId + "\">Remove</a>";

            output.push("<li><strong>", escape(file.name), "</strong> - ", file.size, " bytes. &nbsp; &nbsp; ", removeLink, "</li> ");
        };

        $(this).children(".fileList")
            .append(output.join(""));

        //reset the input to null - nice little chrome bug!
        evt.target.value = null;
    });

    $(this).on("click", ".removeFile", function (e) {
        e.preventDefault();

        var fileId = $(this).parent().children("a").data("fileid");

        // loop through the files array and check if the name of that file matches FileName
        // and get the index of the match
        for (var i = 0; i < filesToUpload.length; ++i) {
            if (filesToUpload[i].id === fileId)
                filesToUpload.splice(i, 1);
        }

        $(this).parent().remove();
    });

    this.clear = function () {
        for (var i = 0; i < filesToUpload.length; ++i) {
            if (filesToUpload[i].id.indexOf(sectionIdentifier) >= 0)
                filesToUpload.splice(i, 1);
        }

        $(this).children(".fileList").empty();
    }

    return this;
};

(function () {
  // getElementById
  function $id(id) {
    return document.getElementById(id);
  }


  function print(e){
    e.preventDefault();
    printid(e);
    printdes(e);
  }
  function printid(e) {
    id = document.getElementById("fid").value;
    Output("<p>File ID:" + id + "</p>");
  }

  function printdes(e) {
    txt = document.getElementById("description").value;
    Output("<p>Description: " + txt + "</p>");
  }
  // output information
  function Output(msg) {
    var m = $id("preview");
    m.innerHTML = m.innerHTML + msg;
  }



  // file selection
  function FileSelectHandler(e) {
    e.preventDefault();
    // fetch FileList object
    var files = e.target.files || e.dataTransfer.files;

    // process all File objects
    for (var i = 0, f; (f = files[i]); i++) {
      ParseFile(f);
    }
  }

  function SignSelectHandler(e) {
    Output("<p>Signature: </p>");

    // fetch FileList object
    var files = e.target.files || e.dataTransfer.files;

    // process all File objects
    for (var i = 0, f; (f = files[i]); i++) {
      ParseFile(f);
    }
  }

  // output file information
  function ParseFile(file) {
    Output(
      "<p>File information: <strong>" +
        file.name +
        "</strong> type: <strong>" +
        file.type +
        "</strong> size: <strong>" +
        file.size +
        "</strong> bytes</p>"
    );

    // display an image
    if (file.type.indexOf("image") == 0) {
      let reader = new FileReader();
      reader.onload = function (e) {
        Output(
          "<p><strong>" +
            file.name +
            ":</strong><br />" +
            '<img src="' +
            e.target.result +
            '" width="200" height="200"/></p>'
        );
      };
      reader.readAsDataURL(file);
    }

    // display text
    if (file.type.indexOf("text") == 0) {
      let reader = new FileReader();
      reader.onload = function (e) {
        Output(
          "<p><strong>" +
            file.name +
            ":</strong></p><pre>" +
            e.target.result.replace(/</g, "&lt;").replace(/>/g, "&gt;") +
            "</pre>"
        );
      };
      reader.readAsText(file);
    }
  }

  // initialize
  function Init() {
    var fileselect = $id("fileselect"),
      signselect = $id("signselect"),
      previewbutton = $id("previewbutton");

    previewbutton.addEventListener("click", print, false);
    fileselect.addEventListener("change", FileSelectHandler, false);
    signselect.addEventListener("change", SignSelectHandler, false);

  }
  if (window.File && window.FileList && window.FileReader) {
    Init();
  }
    var filesToUpload = [];

    var files1Uploader = $("#files1").fileUploader(filesToUpload, "files1");
		var files2Uploader = $("#files2").fileUploader(filesToUpload, "files2");

    $("#uploadBtn").click(function (e) {
        e.preventDefault();

        var formData = new FormData();

        for (var i = 0, len = filesToUpload.length; i < len; i++) {
            formData.append("files", filesToUpload[i].file);
        }

        $.ajax({
            url: "http://requestb.in/1k0dxvs1",
            data: formData,
            processData: false,
            contentType: false,
            type: "POST",
            success: function (data) {
                alert("DONE");

                files1Uploader.clear();
            },
            error: function (data) {
                alert("ERROR - " + data.responseText);
            }
        });
    });
})()
