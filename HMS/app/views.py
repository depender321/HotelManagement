from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest, HttpResponseRedirect,HttpResponse
from django.contrib.messages import warning
from django.template import RequestContext
from django.contrib.auth import logout, authenticate, login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages,auth
from app.forms import RegisterForm, LoginForm, RoomBooking, Reservations
from datetime import datetime
from app.models import UserDetails, RoomBooking, BookingHistory, Rooms
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
from passlib.hash import sha256_crypt
import pymysql
from django.template.defaulttags import register
from django.db.models import Sum
import smtplib
from app.fusioncharts import FusionCharts, FusionTable, TimeSeries
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import OrderedDict

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    global connection, cur, no_of_rooms, rex
    return render(request,'app/index.html')

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(request,'app/contact.html')

def about(request):
    """Renders the about page."""
    return render(request,'app/about.html')

def register(request):
    """Renders the register page."""
    try:
        assert isinstance(request, HttpRequest)
        print("aa")
        if request.method=='POST':
            form = RegisterForm(request.POST)
            print("form")
            if(form.is_valid()):
                print("form2")
                firstname = form['firstname'].value()
                lastname = form['lastname'].value()
                email = form['email'].value()
                address = form['address'].value()
                password = sha256_crypt.encrypt(form['password'].value())
                user_auth = User.objects.create_user(username=email,first_name=firstname,last_name=lastname,email=email,password=password)
                user = UserDetails(email,address,password)
                print(user,"reg")
                user_auth.save()
                user.save()
                return render(request,'app/login.html')
        else:
            form = RegisterForm()
        return render(request,'app/register.html',{'form':form})
    except:
        print("hi")
        return render(request,'app/index.html')

def login(request):
    """Renders the login page"""
    try:
        global rex
        assert isinstance(request, HttpRequest)
        if 'email' in request.session:
            return HttpResponseRedirect('/booking')
        if request.method=='POST':
            form = LoginForm(request.POST)
            if(form.is_valid()):
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                login_cred=UserDetails.objects.filter(email=email).values()
                print(login_cred,"logcred")
                print(login_cred[0])
                det=User.objects.filter(email=email).values()
                print(det,"det")
                dets=[]
                for i in det:
                    for k,v in i.items():
                        print("for")
                        dets.append(v)
                print("before")
                details = login_cred[0]
                print("after")
                superuser = dets[3]
                if email==details['email'] and sha256_crypt.verify(password,details['password']):
                    User.objects.filter(email=email).update(is_active = True)
                    if 'email' not in request.session:
                        request.session['email']=email
                        request.session['hotel']='Hotel Ruby'
                        if superuser:
                            request.session['admin'] = True
                    rex = booking_hist(request,email)
                    return render(request,'app/booking.html',{'superuser':superuser})
                else:
                    # messages.warning(request,'Invalid email/password, Please try again!',extra_tags='alert')
                    print("else")
                    return render(request,'app/login.html')
        else:
            form = LoginForm()
            return render(request,'app/login.html')
    except Exception as e:
        print(e)
        # messages.warning(request,'Invalid email/password, Please try again!')
        return render(request,'app/login.html')

def logout(request):
    try:
        users = User.objects.get(email=request.session['email'])
        users.is_active=False
        users.save()
        del(request.session['email'])
        if 'admin' in request.session:
            del(request.session['admin'])
        return HttpResponseRedirect('/')
    except:
        return HttpResponseRedirect('/login')

def booking(request):
    """Renders the booking page only after the user logs in"""
    try:
        global available_rooms
        if 'email' in request.session:
            return render(request,'app/booking.html')
        else:
            return HttpResponseRedirect('/login')
    except:
        return HttpResponseRedirect('/login')


def roombooking(request):
    try:
        global room_details, cin, cout, rem
        monthDays={'01':31,'02':28,'03':31,'04':30,'05':31,'06':30,'07':31,'08':31,'09':30,'10':31,'11':30,'12':31}
        leapDays={'01':31,'02':29,'03':31,'04':30,'05':31,'06':30,'07':31,'08':31,'09':30,'10':31,'11':30,'12':31}
        room_details = []
        if 'email' in request.session:
            if request.method=='POST':
                form = RoomBooking(request.POST)
                check_in = request.POST.get('checkin')
                cin = changeDateFormat(check_in)
                check_out = request.POST.get('checkout')
                if check_out=='':
                    messages.warning(request,"Checkout date cannot be empty")
                    return render(request,'app/booking.html')
                cout = changeDateFormat(check_out)
                dt1 = check_in.split('/')
                dt2 = check_out.split('/')
                diff=int(dt2[1])-int(dt1[1])
                year = int(dt1[2])
                if(year%4==0 and year%100!=0 or year%400==0):
                    days_comp = leapDays[dt1[0]]
                else:
                    days_comp = monthDays[dt1[0]]
                rem = days_comp
                if diff<0:
                    rem = days_comp+diff
                email = request.session['email']
                hotel_name = request.session['hotel']
                room_details = [cin,cout,email,hotel_name]
                return render(request,'app/rooms.html')
        else:
            print("else")
            return render(request,'app/booking.html')
    except:
        return render(request,'app/index.html')

def single(request):
    try:
        if 'email' in request.session:
            print("first if")
            if request.method=='POST':
                print("second if")
                form = Reservations(request.POST)
                details = get_form(request,form)
                name = details[0]+" "+details[1]+" "+details[2]
                price = rem*1000
                price = price*details[10]
                reservation('single',details,price)
                avl=get_rooms('single')
                avl = len(avl)
                rooms_details = Rooms.objects.filter(roomtype='single').values()
                det=[]
                for i in rooms_details:
                    for k,v in i.items():
                        det.append(v)
                rs = det[2]-details[10]
                if(rs<0):
                    rs = 0
                Rooms.objects.filter(roomtype='single').update(available = rs)
                return render(request,'app/reservation.html',{'name':name,'room':details[10],'cin':cin,'cout':cout,'bid':today_date,'price':price,'roomtype':'Single'})
            else:
                avl=get_rooms('single')
                if len(avl)!=0:
                    return render(request,'app/singlerooms.html',{'avl':avl})
                else:
                    messages.warning(request,'No rooms are available')
                    return render(request,'app/singlerooms.html',{'avl':avl})
        else:
            return render(request,'app/login.html')
    except Exception as e:
        print(e)
        return render(request,'app/reservation.html')
        # return render(request,'app/booking.html')

def double(request):
    try:
        if 'email' in request.session:
            print("Hello")
            if request.method=='POST':
                form = Reservations(request.POST)
                details = get_form(request,form)
                name = details[0]+" "+details[1]+" "+details[2]
                price = rem*1500
                price = price*details[10]
                reservation('double',details,price)
                avl=get_rooms('double')
                avl = len(avl)
                rooms_details = Rooms.objects.filter(roomtype='double').values()
                det=[]
                for i in rooms_details:
                    for k,v in i.items():
                        det.append(v)
                rs = det[2]-details[10]
                if(rs<0):
                    rs = 0
                Rooms.objects.filter(roomtype='double').update(available = rs)
                return render(request,'app/reservation.html',{'name':name,'room':details[10],'cin':cin,'cout':cout,'bid':today_date,'price':price,'roomtype':'Double'})
            else:
                avl=get_rooms('double')
                if len(avl)!=0:
                    return render(request,'app/doublerooms.html',{'avl':avl})
                else:
                    messages.warning(request,'No rooms are available')
                    return render(request,'app/doublerooms.html',{'avl':avl})
        else:
            return render(request,'app/login.html')
    except:
        return render(request,'app/reservation.html')

def deluxe(request):
    try:
        if 'email' in request.session:
            if request.method=='POST':
                form = Reservations(request.POST)
                details = get_form(request,form)
                name = details[0]+" "+details[1]+" "+details[2]
                price = rem*3500
                price = price*details[10]
                reservation('single',details,price)
                avl=get_rooms('single')
                avl = len(avl)
                rooms_details = Rooms.objects.filter(roomtype='single').values()
                det=[]
                for i in rooms_details:
                    for k,v in i.items():
                        det.append(v)
                rs = det[2]-details[10]
                if(rs<0):
                    rs = 0
                Rooms.objects.filter(roomtype='single').update(available = rs)
                return render(request,'app/reservation.html',{'name':name,'room':details[10],'cin':cin,'cout':cout,'bid':today_date,'price':price,'roomtype':'Deluxe'})
            else:
                avl=get_rooms('single')
                if len(avl)!=0:
                    return render(request,'app/deluxe.html',{'avl':avl})
                else:
                    messages.warning(request,'No rooms are available')
                    return render(request,'app/deluxe.html',{'avl':avl})
        else:
            return render(request,'app/login.html')
    except:
        return render(request,'app/booking.html')

def luxury(request):
    try:
        if 'email' in request.session:
            if request.method=='POST':
                form = Reservations(request.POST)
                details = get_form(request,form)
                name = details[0]+" "+details[1]+" "+details[2]
                price = rem*5000
                price = price*details[10]
                reservation('luxury',details,price)
                avl=get_rooms('luxury')
                avl = len(avl)
                rooms_details = Rooms.objects.filter(roomtype='luxury').values()
                det=[]
                for i in rooms_details:
                    for k,v in i.items():
                        det.append(v)
                rs = det[2]-details[10]
                if(rs<0):
                    rs = 0
                Rooms.objects.filter(roomtype='luxury').update(available = rs)
                return render(request,'app/reservation.html',{'name':name,'room':details[10],'cin':cin,'cout':cout,'bid':today_date,'price':price,'roomtype':'Luxury'})
            else:
                avl=get_rooms('luxury')
                if len(avl)!=0:
                    return render(request,'app/luxury.html',{'avl':avl})
                else:
                    messages.warning(request,'No rooms are available')
                    return render(request,'app/luxury.html',{'avl':avl})
        else:
            return render(request,'app/login.html')
    except:
        return render(request,'app/booking.html')

def executive(request):
    try:
        if 'email' in request.session:
            if request.method=='POST':
                form = Reservations(request.POST)
                details = get_form(request,form)
                name = details[0]+" "+details[1]+" "+details[2]
                price = rem*6500
                price = price*details[10]
                reservation('single',details,price)
                avl=get_rooms('single')
                avl = len(avl)
                rooms_details = Rooms.objects.filter(roomtype='single').values()
                det=[]
                for i in rooms_details:
                    for k,v in i.items():
                        det.append(v)
                rs = det[2]-details[10]
                if(rs<0):
                    rs = 0
                Rooms.objects.filter(roomtype='single').update(available = rs)
                return render(request,'app/reservation.html',{'name':name,'room':details[10],'cin':cin,'cout':cout,'bid':today_date,'price':price,'roomtype':'Executive'})
            else:
                avl=get_rooms('single')
                if len(avl)!=0:
                    return render(request,'app/executive.html',{'avl':avl})
                else:
                    messages.warning(request,'No rooms are available')
                    return render(request,'app/executive.html',{'avl':avl})
        else:
            return render(request,'app/login.html')
    except:
        return render(request,'app/booking.html')

def presidential(request):
    try:
        if 'email' in request.session:
            if request.method=='POST':
                form = Reservations(request.POST)
                details = get_form(request,form)
                name = details[0]+" "+details[1]+" "+details[2]
                price = rem*8000
                price = price*details[10]
                reservation('single',details,price)
                avl=get_rooms('single')
                avl = len(avl)
                rooms_details = Rooms.objects.filter(roomtype='single').values()
                det=[]
                for i in rooms_details:
                    for k,v in i.items():
                        det.append(v)
                rs = det[2]-details[10]
                if(rs<0):
                    rs = 0
                Rooms.objects.filter(roomtype='single').update(available = rs)
                return render(request,'app/reservation.html',{'name':name,'room':details[10],'cin':cin,'cout':cout,'bid':today_date,'price':price,'roomtype':'Presidential'})
            else:
                avl=get_rooms('single')
                if len(avl)!=0:
                    return render(request,'app/presidential.html',{'avl':avl})
                else:
                    messages.warning(request,'No rooms are available')
                    return render(request,'app/presidential.html',{'avl':avl})
        else:
            return render(request,'app/login.html')
    except:
        return render(request,'app/booking.html')

def reservation(room,details,price):
        try:
            global today_date
            today_date = int(datetime.now().strftime("%Y%m%d%H%M%S"))
            rb = RoomBooking(today_date,room_details[0],room_details[1],details[0],details[1],details[2],details[3],details[4],details[5],details[6],details[7],details[8],details[9],details[10])
            rb.save()
            user = User.objects.get(email=room_details[2])
            arguments = [today_date,room_details[0],room_details[1],user.email,user.id,price]
            bh = BookingHistory(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5])
            bh.save()
        except:
            return HttpResponseRedirect('/booking')


def update_rooms(roomtype,available,no_of_rooms):
    try:
        rooms_details = Rooms.objects.filter(roomtype=roomtype).values()
        det=[]
        for i in rooms_details:
            for k,v in i.items():
                det.append(v)
        rs = det[2]-det[3]
        if(rs<0):
            rs = 0
        room_details.available = rs
        room_details.save()
    except:
        return render(request,'app/booking.html')

def changeDateFormat(date):
    d_list = date.split('/')
    modified_date = d_list[2]+'-'+d_list[0]+'-'+d_list[1]
    return modified_date

def bookinghistory(request):
    try:
        red = booking_hist(request,request.session['email'])
        return render(request,'app/booking_history.html',{'details':red})
    except:
        return render(request,'app/booking.html')

def booking_hist(request,email):
    try:
        bhr = BookingHistory.objects.filter(email=email).values()
        det=[]
        details = []
        for i in bhr:
            det=[]
            for k,v in i.items():
                det.append(v)
            details.append(det)
        return details
    except:
        return render(request,'app/booking.html')

def forgotpassword(request):
    try:
        if request.method=='POST':
            fromaddr = 'ruby.coders@gmail.com'
            toaddrs  = request.POST.get('email')
            data = UserDetails.objects.filter(email=toaddrs).values()
            msg = 'Hello, your password is P@$sword '
            username = 'ruby.coders@gmail.com'
            password = '$uperSt@r007'
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            server.login(username,password)
            server.sendmail(fromaddr, toaddrs, msg)
            server.quit()
            return redirect(url_for('login'))
        else:
            return render(request,'app/forgotpassword.html')
    except:
        messages.warning(request,'Invalid email please enter valid email')
        return render(request,'app/forgotpassword.html')

def rooms(request):
    assert isinstance(request, HttpRequest)
    return render(request,'app/display_rooms.html')

def adminlogin(request):
    try:
        if 'admin' in request.session:
            return HttpResponseRedirect('/adminruby')
        if request.method=='POST':
            email = request.POST.get('email')
            password = request.POST.get('password')
            login_cred=UserDetails.objects.filter(email=email).values()
            print(login_cred)
            det=User.objects.filter(email=email).values()
            print(det)
            details = login_cred[0]
            dets=[]
            for i in det:
                for k,v in i.items():
                    dets.append(v)
            superuser = dets[3]
            print(superuser)
            if email==details['email'] and sha256_crypt.verify(password,details['password']):
                request.session['email']=email
                reqest.session['admin'] = True
                if superuser:
                    return HttpResponseRedirect('/adminruby')
                else:
                    messages.warning(request,'Not an admin, please contact administrator')
            else:
                messages.warning(request,'Not an admin, please contact administrator')
                return render(request,'app/adminlogin.html')
        else:
            return render(request,'app/adminlogin.html')
    except:
        return render(request,'app/adminlogin.html')


def adminruby(request):
    if 'admin' in request.session:
        dataSource = OrderedDict()
        chartConfig = OrderedDict()
        chartConfig["caption"] = ""
        chartConfig["xAxisName"] = "Rooms"
        chartConfig["yAxisName"] = "Available"
        chartConfig["numberSuffix"] = ""
        chartConfig["theme"] = "fusion"

        chartData = OrderedDict()
        avl1 = len(get_rooms('single'))
        avl2 = len(get_rooms('double'))
        avl3 = len(get_rooms('luxury'))
        avl4 = len(get_rooms('deluxe'))
        avl5 = len(get_rooms('executive'))
        avl6 = len(get_rooms('presidential'))

        chartData["Single"] = avl1
        chartData["Double"] = avl2
        chartData["Deluxe"] = avl3
        chartData["Luxury"] = avl4
        chartData["Executive"] = avl5
        chartData["Presidential"] = avl6

        dataSource["chart"] = chartConfig
        dataSource["data"] = []

        for key, value in chartData.items():
            data = {}
            data["label"] = key
            data["value"] = value
            dataSource["data"].append(data)
        column2D = FusionCharts("column2d", "ex1" , "800", "400", "chart-1", "json", dataSource)
        return  render(request, 'app/adminanalytics.html', {'output' : column2D.render(), 'chartTitle': 'Available Rooms'})
    else:
        return render(request,'app/adminlogin.html')

def getusers(request):
    usr = User.objects.all()
    users=[]
    list2=[]
    for i in usr:
        users.append(i)
    for u in users:
        dets = User.objects.filter(email = u).values()
        list1 =[]
        for k in dets:
            list1.append(k['id'])
            list1.append(k['first_name'])
            list1.append(k['last_name'])
            list1.append(k['email'])
            list1.append(k['date_joined'])
        list2.append(list1)
    return render(request,'app/getusers.html',{'list':list2})

def adminbooking(request):
    try:
        bhr = BookingHistory.objects.all()
        paginator = Paginator(bhr, 10)
        page = request.GET.get('page', 1)
        try:
            bookings = paginator.page(page)
            return render(request,'app/adminbooking.html',{'bookings':bookings})
        except PageNotAnInteger:
            bookings = paginator.page(1)
        except EmptyPage:
            bookings = paginator.page(paginator.num_pages)
            return render(request,'app/adminbooking.html')
    except:
        return render(request,'app/adminruby.html')

def get_form(request,form):
    firstname = form['firstname'].value()
    middlename = form['middlename'].value()
    lastname = form['lastname'].value()
    email = form['email'].value()
    phone = form['phone'].value()
    address = form['address'].value()
    city = form['city'].value()
    state = form['state'].value()
    zipcode = form['zipcode'].value()
    idproof = form['idproof'].value()
    rooms = form['rooms'].value()
    no_of_rooms = int(rooms)
    list = [firstname,middlename,lastname,email,phone,address,city,state,zipcode,idproof,no_of_rooms]
    return list

def get_rooms(roomtype):
    available = Rooms.objects.filter(roomtype=roomtype).values()
    det=[]
    for i in available:
        for k,v in i.items():
            det.append(v)
    avl = det[3]
    available_rooms = avl
    avail= []
    for i in range(1,avl+1):
        avail.append(i)
    return avail

def salesanalysis(request):
    price = BookingHistory.objects.aggregate(Sum('amount'))
    amount = 0
    for k,v in price.items():
        amount = v
    chartObj = FusionCharts( 'angulargauge', 'ex1', '600', '400', 'chart-1', 'json', """{
    "chart": {
    "captionpadding": "0",
    "origw": "320",
    "origh": "300",
    "gaugeouterradius": "115",
    "gaugestartangle": "270",
    "gaugeendangle": "-25",
    "showvalue": "1",
    "valuefontsize": "30",
    "majortmnumber": "13",
    "majortmthickness": "2",
    "majortmheight": "13",
    "minortmheight": "7",
    "minortmthickness": "1",
    "minortmnumber": "1",
    "showgaugeborder": "0",
    "theme": "fusion"
    },
    "colorrange": {
    "color": [
      {
        "minvalue": "0",
        "maxvalue": "5000000",
        "code": "#999999"
      },
      {
        "minvalue": "1500",
        "maxvalue": "10000000",
        "code": "#F6F6F6"
      }
    ]
  },
  "dials": {
    "dial": [
      {
        "value": """+str(amount)+""",
        "bgcolor": "#F20F2F",
        "basewidth": "8"
      }
    ]
  },
  "annotations": {
    "groups": [
      {
        "items": [
          {
            "type": "text",
            "id": "text",
            "text": "INR",
            "x": "$gaugeCenterX",
            "y": "$gaugeCenterY + 40",
            "fontsize": "20",
            "color": "#555555"
          }
        ]
      }
    ]
  }
}""")
    return render(request, 'app/salesanalysis.html', {'output': chartObj.render()})