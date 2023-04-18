
    //  $("body").on("click",function(yy){
    $(document).ready(function() {

        const progressBox = document.getElementById('progress-box')
        const TableStop = document.getElementById('progress-box')
        const csrf_words = document.querySelector("#example input[name='csrfmiddlewaretoken'");
        const csrf_price = document.querySelector("#example4 input[name='csrfmiddlewaretoken'");
        const csrf_brand = document.querySelector("#example2 input[name='csrfmiddlewaretoken'");
        
   

    
    $("#stopwords-form").submit(function (e) {

        e.preventDefault();
        // serialize the data for sending the form data.
        var serializedData = $(this).serialize();
        // Ajax Call

        $.ajax({
            type: 'POST',
            url: "/",
            data: serializedData,
			// handle a successful response
            success: function (response) {
                // On successful, clear all form data
                $("#stopwords-form").trigger('reset');

                // Display new participant to table
                var instance = JSON.parse(response["instance"]);
                var fields = instance[0]["fields"];
                var pk = instance[0]["pk"];
                $("#example tbody").prepend(
                   `<tr class="post-${pk}">
                    <td class="text-center sorting_1">${fields["words"]||""}</td>
                    <td class="text-center sorting_1">
                         <input type="hidden" name="csrfmiddlewaretoken" value="${csrf_words.value}">
                          <button type="button"  class="delete_words" data-id='${pk}' > Удалить  </button>
                        </td>
                    </tr>`
                )
            },     
         
            error: function (response) {
                // alert non successful response
                alert(response["responseJSON"]["error"]);
            }
        });
    });  

 
    $("body").on("click",".delete_words",function(u){
        console.log('удалили')
            u.preventDefault();
            var id = $(this).data('id');
            $.ajax({
                url: "delete/"+id,
                type: 'DELETE',
                dataType: 'json',
                headers: {
                    "X-CSRFTOKEN": csrf_words.value
                },
                data: { id : id },
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_words.value );
                },
                success: function(response){
                    $("#example .post-" + id).remove();
                }
            });
        });  


    $("#brand-form").submit(function (z) {
        // preventing default actions
        z.preventDefault();
        // serialize the data for sending the form data.
        var serializedData = $(this).serialize();
        // Ajax Call
        $.ajax({
            type: 'POST',
            url: "/",
            data: serializedData,
			// handle a successful response
            success: function (response) {
                // On successful, clear all form data
                $("#brand-form").trigger('reset');

                // Display new participant to table
                var instance = JSON.parse(response["instance"]);
                var fields = instance[0]["fields"];
                var pk = instance[0]["pk"];
                $("#example2 tbody").prepend(
                   `<tr class="post-${pk}">
                    <td class="text-center sorting_1">${fields["brand"]||""}</td>
                    <td class="text-center sorting_1">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrf_brand.value}">
                    <button type="button"  class="delete_buttonbr" data-id='${pk}' > Удалить  </button>
                        </td>
                    </tr>`
                );
            },     
         
            error: function (response) {
                // alert non successful response
                alert(response["responseJSON"]["error"]);
            }
        });
    });

    $("#price-forms").submit(function (a) {
        progressBox.classList.remove('not-visible')
        // preventing default actions
        a.preventDefault();
        $form = $(this);
        var formData = new FormData(this);
        // serialize the data for sending the form data.
        var serializedData = $(this).serialize();
        // console.log(serializedData);
        // Ajax Call
        $.ajax({
            type: 'POST',
            url: "/",
            data: formData,

            xhr: function(){
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', e=>{
                    // console.log(e)
                    if (e.lengthComputable) {
                        const percent = e.loaded / e.total * 100
                        console.log(percent)
                        progressBox.innerHTML = `
                        <div class="h-1 bg-blue-500" style="width:${percent}%"></div>`
                    }
                })
                    return xhr
            },

            success: function (response) {
                progressBox.classList.add('not-visible')
                $("#price-forms").trigger('reset');
                var instance = JSON.parse(response["instance"]);
                var data = (response["data"]);
                // console.log(data)
                var fields = instance[0]["fields"];
                var pk = instance[0]["pk"];
                $("#example4 tbody").prepend(
                   `<tr class="post-${data["pk"]}">
                    <td class="text-center sorting_1">${fields["files"]||""}</td>
                    <td class="text-center sorting_1">${data["brend_field"]||""}</td>

                    <td class="text-center sorting_1">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrf_price.value}">
                            <button type="button"  class="delete_price" data-id="${data["pk"]}" > Удалить </button>
                        </td>
                    </tr>`
                );
                
             },
             error: function (response) {
                console.log(response,'произошла ошибка')
             },
            cache: false,
            contentType: false,
            processData: false
        });
    });
   
    $("body").on("click",".delete_buttonbr",function(u){
            u.preventDefault();
            var id = $(this).data('id');
            $.ajax({
                url: "delbr/"+id,
                type: 'DELETE',
                dataType: 'json',
                headers: {
                    "X-CSRFTOKEN": csrf_brand.value
                },
                data: { id : id },
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_brand.value );
                },
                success: function(response){
                    $("#example2 .post-" + id).remove();
                }
            });
        });


        $("body").on("click",".delete_price",function(u){
            u.preventDefault();
            var id = $(this).data('id');
            $.ajax({
                url: "delpr/"+id,
                type: 'DELETE',
                dataType: 'json',
                headers: {
                    "X-CSRFTOKEN": csrf_price.value
                },
                data: { id : id },
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_price.value );
                },
                success: function(response){
                    $("#example4 .post-" + id).remove();
                }
            });
        });
    });