from django.shortcuts import render, redirect
from . models import *
from django.http import JsonResponse
import json
import datetime
from .utils import cookieCart, cartData, guestOrder
from .forms import SignUpForm, LoginForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

def loginUser(request):
    if request.method == 'POST':

        form=AuthenticationForm(data=request.POST)
        if form.is_valid():
            user=form.get_user()
            FirstName=(user.first_name)
            username=form.cleaned_data.get('username')
            login(request, user)

            # username=request.POST['username']
            # password=request.POST['password']
            #
            # user = authenticate(request, username=username, password=password)
            # print (user)
            # if user is not None:
            #     login(request, user)

            customer = Customer.objects.get(name = FirstName)
            customer.user = request.user
            customer.save()
            messages.success(request, f'logged in successfully {username}!')

            return redirect('store')
        else:
            form = AuthenticationForm()
            return render(request, 'store/signup.html', {'form':form})
    else:
        form=AuthenticationForm()
    context = {'form':form}
    return render(request, 'store/login.html', context)

def SignUp(request):
    if request.method == 'POST':
        form=SignUpForm(request.POST)
        if form.is_valid():
            form.save(commit=False)
            user = form.cleaned_data.get('username')
            name = form.cleaned_data.get('first_name')
            email = form.cleaned_data.get('email')
            messages.success(request, 'Account was created for ' + user)
            customer = Customer.objects.create(
                email=email, name=name
            )
            customer.save()
            form.save()
            return redirect('login')
    else:
        form=SignUpForm()
    context = {'form':form}
    return render(request, 'store/signup.html', context)

def LogOut(request):
    logout(request)
    return redirect('/')

# @login_required(login_url='login/')
def store(request):

    print (request.user)
    data = cartData(request)

    cartItems = data['cartItems']

    products = Product.objects.all()
    context = {'products':products, 'cartItems':cartItems}
    return render(request, 'store/store.html', context)

def cart(request):
    if request.method == "POST":
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        order.delete()
        return redirect ('store')

    data = cartData(request)
    items = data["items"]
    cartItems = data['cartItems']
    order = data['order']

    context = {"items":items, "order":order, 'cartItems':cartItems}
    return render(request, "store/cart.html", context)

def checkout(request):

    data = cartData(request)
    items = data["items"]
    cartItems = data['cartItems']
    order = data['order']

    context = {"items":items, "order":order, 'cartItems':cartItems}
    return render(request, "store/checkout.html", context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    # print (data)
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)
#
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True
    order.save()

    if order.shipping == True:
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=data['shipping']['address'],
                city=data['shipping']['address'],
                state=data['shipping']['address'],
                zipcode=data['shipping']['address'],
            )

    return JsonResponse('payment complete!', safe=False)
